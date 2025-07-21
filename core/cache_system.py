"""
Sistema de Cache Inteligente
MoveMarias - Cache adaptativo para melhor performance
"""

import hashlib
import json
from functools import wraps
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class SmartCache:
    """Sistema de cache inteligente com invalidação automática"""
    
    def __init__(self, prefix='mm_cache'):
        self.prefix = prefix
        # Handle both dictionary and integer timeout settings
        cache_timeout = getattr(settings, 'CACHE_TIMEOUT', 300)
        if isinstance(cache_timeout, dict):
            self.default_timeout = cache_timeout.get('MEDIUM', 300)
            self.timeout_options = cache_timeout
        else:
            self.default_timeout = cache_timeout
            self.timeout_options = {
                'SHORT': 300,
                'MEDIUM': 1800,
                'LONG': 3600,
                'VERY_LONG': 86400
            }
    
    def _make_key(self, key):
        """Cria uma chave única para o cache"""
        return f"{self.prefix}:{key}"
    
    def _serialize_args(self, args, kwargs):
        """Serializa argumentos para criar chave única"""
        try:
            serialized = json.dumps({
                'args': args,
                'kwargs': sorted(kwargs.items())
            }, sort_keys=True)
            return hashlib.md5(serialized.encode()).hexdigest()
        except (TypeError, ValueError):
            # Se não conseguir serializar, usa hash dos objetos
            return hashlib.md5(str(args + tuple(sorted(kwargs.items()))).encode()).hexdigest()
    
    def get(self, key, default=None):
        """Recupera valor do cache"""
        cache_key = self._make_key(key)
        return cache.get(cache_key, default)
    
    def set(self, key, value, timeout=None):
        """Armazena valor no cache"""
        cache_key = self._make_key(key)
        timeout = timeout or self.default_timeout
        
        # Ensure timeout is an integer
        if isinstance(timeout, dict):
            timeout = timeout.get('MEDIUM', 300)
        
        # Adiciona metadados
        cached_data = {
            'value': value,
            'timestamp': timezone.now().isoformat(),
            'timeout': timeout
        }
        
        cache.set(cache_key, cached_data, timeout)
        logger.debug(f"Cache set: {cache_key} (timeout: {timeout}s)")
    
    def delete(self, key):
        """Remove valor do cache"""
        cache_key = self._make_key(key)
        cache.delete(cache_key)
        logger.debug(f"Cache deleted: {cache_key}")
    
    def clear_pattern(self, pattern):
        """Remove todos os valores que correspondem ao padrão"""
        # Nota: Esta funcionalidade depende do backend de cache
        # Redis suporta, mas memcached não
        try:
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern(f"{self.prefix}:{pattern}")
            else:
                logger.warning("Cache backend doesn't support pattern deletion")
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {e}")
    
    def get_or_set(self, key, callable_func, timeout=None):
        """Recupera do cache ou executa função e armazena resultado"""
        cached_data = self.get(key)
        
        if cached_data is not None:
            return cached_data['value']
        
        # Executa função e armazena resultado
        result = callable_func()
        self.set(key, result, timeout)
        return result
    
    def cached_method(self, timeout=None, key_func=None):
        """Decorator para cache de métodos"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Gera chave única para cache
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._serialize_args(args, kwargs)
                
                # Verifica se valor está em cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached_value['value']
                
                # Executa função e armazena no cache
                result = func(*args, **kwargs)
                self.set(cache_key, result, timeout)
                logger.debug(f"Cache miss: {cache_key}")
                return result
            
            return wrapper
        return decorator
    
    def __call__(self, timeout=None, key_func=None):
        """Make the SmartCache instance callable as a decorator"""
        return self.cached_method(timeout, key_func)


class ModelCache:
    """Sistema de cache específico para modelos Django"""
    
    def __init__(self, model_class):
        self.model_class = model_class
        self.cache = SmartCache(f'model_{model_class._meta.label_lower}')
    
    def get_object(self, pk):
        """Recupera objeto do cache por PK"""
        key = f"object_{pk}"
        return self.cache.get(key)
    
    def set_object(self, obj, timeout=None):
        """Armazena objeto no cache"""
        key = f"object_{obj.pk}"
        self.cache.set(key, obj, timeout)
    
    def delete_object(self, pk):
        """Remove objeto do cache"""
        key = f"object_{pk}"
        self.cache.delete(key)
    
    def get_queryset(self, query_key, timeout=None):
        """Recupera queryset do cache"""
        key = f"queryset_{query_key}"
        return self.cache.get(key)
    
    def set_queryset(self, query_key, queryset, timeout=None):
        """Armazena queryset no cache"""
        key = f"queryset_{query_key}"
        # Converte queryset para lista para serialização
        data = list(queryset.values())
        self.cache.set(key, data, timeout)
    
    def invalidate_all(self):
        """Invalida todo o cache do modelo"""
        self.cache.clear_pattern('*')


class ViewCache:
    """Sistema de cache para views"""
    
    def __init__(self):
        self.cache = SmartCache('view_cache')
    
    def cache_page(self, timeout=None, key_func=None):
        """Decorator para cachear resposta de view"""
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                # Gera chave baseada na view e parâmetros
                if key_func:
                    cache_key = key_func(request, *args, **kwargs)
                else:
                    view_name = view_func.__name__
                    user_id = request.user.id if request.user.is_authenticated else 'anonymous'
                    params = self.cache._serialize_args(args, kwargs)
                    cache_key = f"{view_name}:{user_id}:{params}"
                
                # Tenta recuperar do cache
                cached_response = self.cache.get(cache_key)
                if cached_response is not None:
                    return cached_response['value']
                
                # Executa view e armazena resultado
                response = view_func(request, *args, **kwargs)
                
                # Só cacheia se a resposta for bem-sucedida
                if hasattr(response, 'status_code') and response.status_code == 200:
                    self.cache.set(cache_key, response, timeout)
                
                return response
            
            return wrapper
        return decorator


# Instâncias globais
smart_cache = SmartCache()
view_cache = ViewCache()

# Funções utilitárias
def cache_key_user(user_id, key):
    """Gera chave de cache específica para usuário"""
    return f"user_{user_id}:{key}"

def cache_key_model(model_class, key):
    """Gera chave de cache específica para modelo"""
    return f"model_{model_class._meta.label_lower}:{key}"

def invalidate_user_cache(user_id):
    """Invalida cache específico de um usuário"""
    smart_cache.clear_pattern(f"user_{user_id}:*")

def invalidate_model_cache(model_class):
    """Invalida cache específico de um modelo"""
    smart_cache.clear_pattern(f"model_{model_class._meta.label_lower}:*")

# Decorators
def cached(timeout=300, key_func=None):
    """Decorator para cachear resultado de função"""
    return smart_cache.cached_method(timeout, key_func)

def cached_property(timeout=300):
    """Decorator para cachear propriedade de classe"""
    def decorator(func):
        @wraps(func)
        def wrapper(self):
            cache_key = f"{self.__class__.__name__}_{id(self)}_{func.__name__}"
            cached_value = smart_cache.get(cache_key)
            
            if cached_value is not None:
                return cached_value['value']
            
            result = func(self)
            smart_cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator

# Middleware para cache automático
class CacheMiddleware:
    """Middleware para cache automático de responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache = SmartCache('middleware_cache')
    
    def __call__(self, request):
        # Verifica se deve usar cache
        if self.should_cache(request):
            cache_key = self.get_cache_key(request)
            cached_response = self.cache.get(cache_key)
            
            if cached_response is not None:
                return cached_response['value']
        
        response = self.get_response(request)
        
        # Armazena no cache se apropriado
        if self.should_cache(request) and hasattr(response, 'status_code') and response.status_code == 200:
            cache_key = self.get_cache_key(request)
            self.cache.set(cache_key, response, 300)  # 5 minutos
        
        return response
    
    def should_cache(self, request):
        """Determina se a requisição deve ser cacheada"""
        # Não cacheia POST, PUT, DELETE
        if request.method not in ['GET', 'HEAD']:
            return False
        
        # Não cacheia se há parâmetros de query específicos
        if 'nocache' in request.GET:
            return False
        
        # Não cacheia admin
        if request.path.startswith('/admin/'):
            return False
        
        return True
    
    def get_cache_key(self, request):
        """Gera chave de cache para requisição"""
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        path = request.path
        query_params = sorted(request.GET.items())
        
        key_data = {
            'user_id': user_id,
            'path': path,
            'query_params': query_params
        }
        
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

# Sistema de warm-up de cache
class CacheWarmup:
    """Sistema para pré-carregar cache com dados frequentemente acessados"""
    
    def __init__(self):
        self.cache = SmartCache('warmup_cache')
    
    def warmup_user_data(self, user_id):
        """Pré-carrega dados do usuário"""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            
            # Cacheia dados básicos do usuário
            user_cache_key = cache_key_user(user_id, 'basic_data')
            self.cache.set(user_cache_key, {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }, 3600)  # 1 hora
            
            logger.info(f"Warmed up cache for user {user_id}")
            
        except User.DoesNotExist:
            logger.warning(f"User {user_id} not found for cache warmup")
    
    def warmup_dashboard_data(self):
        """Pré-carrega dados do dashboard"""
        # Aqui você carregaria dados estatísticos do dashboard
        # que são frequentemente acessados
        pass

# Instância global
cache_warmup = CacheWarmup()
