from django.middleware.csrf import get_token
from django.conf import settings
from .unified_permissions import get_user_permissions

def csrf_token_processor(request):
    """
    Custom context processor to ensure CSRF token is always available
    """
    return {
        'csrf_token': get_token(request),
        'csrf_token_value': get_token(request),
    }

def global_context(request):
    """
    Global context processor para adicionar variáveis globais aos templates
    """
    return {
        'site_name': 'MoveMarias',
        'environment': getattr(settings, 'ENVIRONMENT', 'development'),
        'debug': settings.DEBUG,
        'version': '3.0.0',  # Sprint 3
    }

def unified_permissions(request):
    """
    Adiciona permissões unificadas ao contexto dos templates
    """
    if request.user.is_authenticated:
        # Obter permissões do usuário
        permissions = get_user_permissions(request.user)
        
        # Contar notificações não lidas
        unread_notifications = 0
        try:
            from notifications.models import Notification
            unread_notifications = Notification.objects.filter(
                recipient=request.user, 
                status='pending'
            ).count()
        except:
            pass
        
        return {
            'perms': permissions['modules'],
            'user_permissions': permissions,
            'unread_notifications_count': unread_notifications,
        }
    
    return {
        'perms': {},
        'user_permissions': {
            'is_technician': False,
            'is_coordinator': False,
            'is_admin': False,
            'modules': {}
        },
        'unread_notifications_count': 0,
    }

def permissions_context_processor(request):
    """
    Context processor para sistema de permissões
    Alias para a função unified_permissions para compatibilidade
    """
    return unified_permissions(request)
