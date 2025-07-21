"""
Sistema de cache inteligente para performance otimizada
"""
from django.core.cache import cache
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging
from functools import wraps
import hashlib
import json

logger = logging.getLogger('performance')

class SmartCacheManager:
    """
    Gerenciador de cache inteligente com invalidação automática
    """
    
    # Configurações de timeout por tipo de dados
    CACHE_TIMEOUTS = {
        'critical': 60,      # 1 minuto - dados críticos
        'short': 300,        # 5 minutos - dados dinâmicos  
        'medium': 1800,      # 30 minutos - dados estáveis
        'long': 3600,        # 1 hora - dados semi-estáticos
        'very_long': 86400,  # 24 horas - dados estáticos
    }
    
    # Prefixos por módulo para organização
    CACHE_PREFIXES = {
        'beneficiaries': 'ben',
        'workshops': 'wsh', 
        'projects': 'prj',
        'dashboard': 'dash',
        'users': 'usr',
        'stats': 'stats'
    }
    
    @classmethod
    def get_cache_key(cls, prefix, identifier, suffix=''):
        """Gera chave de cache padronizada"""
        key_parts = [cls.CACHE_PREFIXES.get(prefix, prefix), str(identifier)]
        if suffix:
            key_parts.append(suffix)
        return ':'.join(key_parts)
    
    @classmethod
    def set_cache(cls, key, value, timeout_type='medium'):
        """Define valor no cache com timeout apropriado"""
        timeout = cls.CACHE_TIMEOUTS.get(timeout_type, 1800)
        cache.set(key, value, timeout)
        logger.info(f"Cache set: {key} (timeout: {timeout}s)")
    
    @classmethod
    def get_cache(cls, key, default=None):
        """Obtém valor do cache com log"""
        value = cache.get(key, default)
        status = 'hit' if value is not None else 'miss'
        logger.info(f"Cache {status}: {key}")
        return value
    
    @classmethod
    def invalidate_pattern(cls, pattern):
        """Invalida chaves que correspondem ao padrão"""
        # Em produção, usar Redis KEYS ou SCAN
        # Para desenvolvimento, invalidação manual
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(pattern)
        else:
            # Fallback para cache local
            cache.clear()
        logger.info(f"Cache invalidated: {pattern}")
    
    @classmethod
    def invalidate_beneficiary(cls, beneficiary_id):
        """Invalida cache relacionado a beneficiária"""
        patterns = [
            cls.get_cache_key('beneficiaries', beneficiary_id),
            cls.get_cache_key('beneficiaries', 'list'),
            cls.get_cache_key('dashboard', 'stats'),
            cls.get_cache_key('stats', 'beneficiaries')
        ]
        for pattern in patterns:
            cache.delete(pattern)
        logger.info(f"Beneficiary cache invalidated: {beneficiary_id}")
    
    @classmethod
    def invalidate_workshop(cls, workshop_id):
        """Invalida cache relacionado a workshop"""
        patterns = [
            cls.get_cache_key('workshops', workshop_id),
            cls.get_cache_key('workshops', 'list'),
            cls.get_cache_key('dashboard', 'stats'),
            cls.get_cache_key('stats', 'workshops')
        ]
        for pattern in patterns:
            cache.delete(pattern)
        logger.info(f"Workshop cache invalidated: {workshop_id}")


def smart_cache(timeout_type='medium', key_prefix='', invalidate_on=None):
    """
    Decorator para cache inteligente com invalidação automática
    
    Args:
        timeout_type: Tipo de timeout ('critical', 'short', 'medium', 'long', 'very_long')
        key_prefix: Prefixo da chave de cache
        invalidate_on: Lista de sinais que invalidam o cache
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave única baseada na função e argumentos
            func_name = f"{func.__module__}.{func.__name__}"
            args_key = hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()[:8]
            cache_key = f"{key_prefix}:{func_name}:{args_key}" if key_prefix else f"{func_name}:{args_key}"
            
            # Tentar obter do cache
            result = SmartCacheManager.get_cache(cache_key)
            if result is not None:
                return result
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            SmartCacheManager.set_cache(cache_key, result, timeout_type)
            
            return result
        return wrapper
    return decorator


class QueryOptimizer:
    """
    Otimizador de queries com cache e prefetch inteligente
    """
    
    @staticmethod
    def optimize_beneficiary_list():
        """Query otimizada para lista de beneficiárias"""
        from members.models import Beneficiary
        from django.db.models import Count, Prefetch
        
        return Beneficiary.objects.prefetch_related(
            Prefetch(
                'workshop_enrollments',
                queryset=WorkshopEnrollment.objects.select_related('workshop')
            ),
            Prefetch(
                'project_enrollments',
                queryset=ProjectEnrollment.objects.select_related('project')
            ),
            'evolution_records'
        ).annotate(
            workshop_count=Count('workshop_enrollments', distinct=True),
            project_count=Count('project_enrollments', distinct=True)
        )
    
    @staticmethod
    def optimize_workshop_list():
        """Query otimizada para lista de workshops"""
        from workshops.models import Workshop
        from django.db.models import Count
        
        return Workshop.objects.prefetch_related(
            'enrollments__beneficiary',
            'sessions'
        ).annotate(
            participant_count=Count('enrollments', distinct=True),
            session_count=Count('sessions', distinct=True)
        )
    
    @staticmethod 
    def optimize_dashboard_stats():
        """Query otimizada para estatísticas do dashboard"""
        from members.models import Beneficiary
        from workshops.models import Workshop
        from projects.models import Project
        from django.db.models import Count, Q
        from django.utils import timezone
        
        now = timezone.now()
        last_week = now.date() - timezone.timedelta(days=7)
        
        return {
            'beneficiaries': Beneficiary.objects.aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(status='ATIVA')),
                new_week=Count('id', filter=Q(created_at__date__gte=last_week))
            ),
            'workshops': Workshop.objects.aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(status='ativo'))
            ),
            'projects': Project.objects.aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(status='ATIVO'))
            )
        }


# Decorators pré-configurados para casos comuns
dashboard_cache = smart_cache(timeout_type='short', key_prefix='dashboard')
list_cache = smart_cache(timeout_type='medium', key_prefix='list')
detail_cache = smart_cache(timeout_type='long', key_prefix='detail')
stats_cache = smart_cache(timeout_type='short', key_prefix='stats')


# Signal receivers para invalidação automática
@receiver(post_save, sender='members.Beneficiary')
def invalidate_beneficiary_cache(sender, instance, **kwargs):
    """Invalida cache quando beneficiária é modificada"""
    SmartCacheManager.invalidate_beneficiary(instance.id)


@receiver(post_save, sender='workshops.Workshop')
def invalidate_workshop_cache(sender, instance, **kwargs):
    """Invalida cache quando workshop é modificado"""
    SmartCacheManager.invalidate_workshop(instance.id)


@receiver(post_delete, sender='members.Beneficiary')
def invalidate_beneficiary_cache_on_delete(sender, instance, **kwargs):
    """Invalida cache quando beneficiária é deletada"""
    SmartCacheManager.invalidate_beneficiary(instance.id)


@receiver(post_delete, sender='workshops.Workshop')
def invalidate_workshop_cache_on_delete(sender, instance, **kwargs):
    """Invalida cache quando workshop é deletado"""
    SmartCacheManager.invalidate_workshop(instance.id)


class PerformanceMonitor:
    """
    Monitor de performance para queries e cache
    """
    
    def __init__(self):
        self.query_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def log_query(self, query, time_taken):
        """Log de query executada"""
        self.query_count += 1
        logger.info(f"Query #{self.query_count}: {time_taken:.3f}s - {str(query)[:100]}")
    
    def log_cache_hit(self, key):
        """Log de cache hit"""
        self.cache_hits += 1
        logger.info(f"Cache HIT: {key} (total hits: {self.cache_hits})")
    
    def log_cache_miss(self, key):
        """Log de cache miss"""
        self.cache_misses += 1
        logger.info(f"Cache MISS: {key} (total misses: {self.cache_misses})")
    
    def get_stats(self):
        """Retorna estatísticas de performance"""
        total_cache_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0
        
        return {
            'query_count': self.query_count,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': hit_rate
        }


# Instância global do monitor
performance_monitor = PerformanceMonitor()
