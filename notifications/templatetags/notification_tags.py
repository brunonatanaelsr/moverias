from django import template
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from ..models import Notification

register = template.Library()

@register.filter(name='add_class')
def add_class(value, css_class):
    """
    Adiciona uma classe CSS a um campo de formulário
    """
    if hasattr(value, 'widget'):
        # Se é um campo de formulário
        existing_classes = value.widget.attrs.get('class', '')
        if existing_classes:
            value.widget.attrs['class'] = f"{existing_classes} {css_class}"
        else:
            value.widget.attrs['class'] = css_class
    return value


@register.filter(name='notification_icon')
def notification_icon(notification_type):
    """
    Retorna o ícone correspondente ao tipo de notificação
    """
    icons = {
        'welcome': 'fas fa-star',
        'workshop_enrollment': 'fas fa-calendar-plus',
        'workshop_reminder': 'fas fa-bell',
        'certificate_ready': 'fas fa-certificate',
        'project_invitation': 'fas fa-users',
        'coaching_scheduled': 'fas fa-comments',
        'system_update': 'fas fa-cog',
        'password_reset': 'fas fa-key',
        'account_verification': 'fas fa-check-circle',
        'general': 'fas fa-info-circle',
    }
    return icons.get(notification_type, 'fas fa-info-circle')


@register.filter(name='notification_color')
def notification_color(notification_type):
    """
    Retorna a cor correspondente ao tipo de notificação
    """
    colors = {
        'welcome': 'primary',
        'workshop_enrollment': 'success',
        'workshop_reminder': 'warning',
        'certificate_ready': 'info',
        'project_invitation': 'secondary',
        'coaching_scheduled': 'warning',
        'system_update': 'dark',
        'password_reset': 'danger',
        'account_verification': 'success',
        'general': 'info',
    }
    return colors.get(notification_type, 'info')


@register.filter(name='priority_class')
def priority_class(priority):
    """
    Retorna a classe CSS correspondente à prioridade
    """
    classes = {
        1: 'priority-low',
        2: 'priority-normal',
        3: 'priority-high',
        4: 'priority-urgent',
    }
    return classes.get(priority, 'priority-normal')


@register.filter(name='is_important')
def is_important(notification):
    """
    Verifica se a notificação está marcada como importante
    """
    if hasattr(notification, 'metadata') and notification.metadata:
        return notification.metadata.get('is_important', False)
    return False


@register.inclusion_tag('notifications/components/notification_card.html')
def notification_card(notification, show_actions=True):
    """
    Renderiza um card de notificação
    """
    return {
        'notification': notification,
        'show_actions': show_actions,
    }


@register.inclusion_tag('notifications/components/notification_counter.html')
def notification_counter(user):
    """
    Renderiza contador de notificações não lidas
    """
    count = Notification.objects.filter(
        recipient=user,
        status='pending'
    ).count()
    
    return {
        'count': count,
        'user': user,
    }


@register.simple_tag
def notification_stats(user):
    """
    Retorna estatísticas de notificações do usuário
    """
    notifications = Notification.objects.filter(recipient=user)
    
    return {
        'total': notifications.count(),
        'unread': notifications.filter(status='pending').count(),
        'read': notifications.filter(status='read').count(),
        'important': notifications.filter(
            metadata__is_important=True
        ).count(),
    }


@register.simple_tag
def get_notification_url(notification, action='detail'):
    """
    Retorna a URL para uma ação específica da notificação
    """
    from django.urls import reverse
    
    urls = {
        'detail': 'notifications:detail',
        'edit': 'notifications:edit',
        'delete': 'notifications:delete',
        'mark_read': 'notifications:mark_read',
        'mark_important': 'notifications:mark_important',
    }
    
    url_name = urls.get(action)
    if url_name:
        return reverse(url_name, kwargs={'pk': notification.pk if action in ['detail', 'edit', 'delete'] else notification.id})
    return '#'
