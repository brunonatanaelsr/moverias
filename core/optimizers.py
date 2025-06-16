"""
Otimizações de performance para queries do Django
"""
from django.db.models import Prefetch, Q, Count, Avg, Sum, Max
from django.core.cache import cache
from django.conf import settings


class QueryOptimizer:
    """
    Classe utilitária para optimização de queries
    """
    
    @staticmethod
    def get_beneficiaries_optimized():
        """
        Query otimizada para beneficiárias com relacionamentos
        """
        from members.models import Beneficiary
        
        return Beneficiary.objects.select_related(
            # Não há relacionamentos diretos para select_related
        ).prefetch_related(
            # Projetos com status ativo
            Prefetch(
                'project_enrollments',
                queryset=None,  # Será definido quando o modelo estiver disponível
                to_attr='active_projects'
            ),
            # Anamneses sociais
            Prefetch(
                'social_anamneses',
                queryset=None,  # Será definido quando o modelo estiver disponível
                to_attr='recent_anamneses'
            ),
            # Registros de evolução
            Prefetch(
                'evolution_records',
                queryset=None,  # Será definido quando o modelo estiver disponível
                to_attr='recent_evolutions'
            )
        )
    
    @staticmethod
    def get_projects_optimized():
        """
        Query otimizada para projetos com beneficiárias
        """
        from projects.models import ProjectEnrollment
        
        return ProjectEnrollment.objects.select_related(
            'beneficiary'
        ).annotate(
            # Adicionar estatísticas calculadas
            attendance_count=Count('beneficiary__evolution_records', distinct=True)
        )
    
    @staticmethod
    def get_workshops_optimized():
        """
        Query otimizada para workshops com sessões e inscrições
        """
        from workshops.models import Workshop, WorkshopSession, WorkshopEnrollment
        
        return Workshop.objects.prefetch_related(
            # Sessões ordenadas
            Prefetch(
                'sessions',
                queryset=WorkshopSession.objects.order_by('session_number'),
                to_attr='ordered_sessions'
            ),
            # Inscrições ativas com beneficiárias
            Prefetch(
                'enrollments',
                queryset=WorkshopEnrollment.objects.select_related(
                    'beneficiary'
                ).filter(status='ativo'),
                to_attr='active_enrollments'
            )
        ).annotate(
            # Estatísticas agregadas
            total_sessions=Count('sessions', distinct=True),
            active_participants=Count(
                'enrollments',
                filter=Q(enrollments__status='ativo'),
                distinct=True
            )
        )
    
    @staticmethod
    def get_evolution_records_optimized():
        """
        Query otimizada para registros de evolução
        """
        from evolution.models import EvolutionRecord
        
        return EvolutionRecord.objects.select_related(
            'beneficiary',
            'author',
            'signed_by_beneficiary'
        ).order_by('-date')
    
    @staticmethod
    def get_social_anamneses_optimized():
        """
        Query otimizada para anamneses sociais
        """
        from social.models import SocialAnamnesis
        
        return SocialAnamnesis.objects.select_related(
            'beneficiary',
            'created_by'
        ).order_by('-created_at')
    
    @staticmethod
    def get_users_optimized():
        """
        Query otimizada para usuários com perfis e atividades
        """
        from django.contrib.auth import get_user_model
        from users.models import UserActivity
        
        User = get_user_model()
        
        return User.objects.select_related(
            'profile'
        ).prefetch_related(
            # Atividades recentes
            Prefetch(
                'activities',
                queryset=UserActivity.objects.order_by('-timestamp')[:10],
                to_attr='recent_activities'
            ),
            'groups',
            'user_permissions'
        ).annotate(
            # Estatísticas de atividade
            activity_count=Count('activities', distinct=True),
            last_activity=Max('activities__timestamp')
        )


class CacheManager:
    """
    Gerenciador de cache para operações frequentes
    """
    
    @staticmethod
    def get_or_set_cache(key, callable_func, timeout=None):
        """
        Utilitário genérico para cache
        """
        if timeout is None:
            timeout = getattr(settings, 'CACHE_TIMEOUT', {}).get('MEDIUM', 1800)
        
        data = cache.get(key)
        if data is None:
            data = callable_func()
            cache.set(key, data, timeout)
        
        return data
    
    @staticmethod
    def get_dashboard_stats(user_id):
        """
        Cache para estatísticas do dashboard
        """
        cache_key = f'dashboard_stats_{user_id}'
        
        def _get_stats():
            from members.models import Beneficiary
            from projects.models import ProjectEnrollment
            from workshops.models import Workshop
            from users.models import UserActivity
            
            return {
                'total_beneficiaries': Beneficiary.objects.count(),
                'active_projects': ProjectEnrollment.objects.filter(
                    status='ATIVO'
                ).count(),
                'total_workshops': Workshop.objects.count(),
                'recent_activities': UserActivity.objects.order_by(
                    '-timestamp'
                )[:5]
            }
        
        return CacheManager.get_or_set_cache(
            cache_key, 
            _get_stats,
            timeout=settings.CACHE_TIMEOUT.get('SHORT', 300)
        )
    
    @staticmethod
    def invalidate_related_cache(model_name, instance_id=None):
        """
        Invalidar caches relacionados quando um modelo é atualizado
        """
        patterns = {
            'beneficiary': [
                'dashboard_stats_*',
                'beneficiaries_list_*',
                f'beneficiary_{instance_id}' if instance_id else 'beneficiary_*'
            ],
            'project': [
                'dashboard_stats_*',
                'projects_list_*',
                f'project_enrollment_{instance_id}' if instance_id else 'project_*'
            ],
            'workshop': [
                'dashboard_stats_*',
                'workshops_list_*',
                f'workshop_{instance_id}' if instance_id else 'workshop_*'
            ]
        }
        
        if model_name.lower() in patterns:
            for pattern in patterns[model_name.lower()]:
                if '*' in pattern:
                    # Para padrões com wildcard, seria necessário usar Redis
                    # Por enquanto, limpar cache específico
                    cache.delete(pattern.replace('*', ''))
                else:
                    cache.delete(pattern)


class PaginationOptimizer:
    """
    Otimizações para paginação eficiente
    """
    
    @staticmethod
    def optimize_queryset_for_pagination(queryset, page_size=20):
        """
        Otimizar queryset para paginação
        """
        # Usar only() para campos necessários na listagem
        # Usar defer() para campos pesados não necessários
        return queryset.select_related().prefetch_related()
    
    @staticmethod
    def get_efficient_page_count(queryset):
        """
        Contar registros de forma eficiente
        """
        # Para queries complexas, usar aproximação
        try:
            return queryset.count()
        except:
            # Fallback para queries muito complexas
            return len(queryset)
