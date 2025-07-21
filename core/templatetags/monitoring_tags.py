"""
Template tags para widgets de monitoramento
"""
from django import template
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from core.monitoring import get_system_health, get_database_health
from core.background_jobs import get_job_stats
from django.template.loader import render_to_string
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import json

register = template.Library()

@register.inclusion_tag('monitoring/widgets/system_status.html', takes_context=True)
def system_status_widget(context, size='medium'):
    """Widget de status do sistema"""
    request = context.get('request')
    
    if not request or not request.user.is_authenticated:
        return {'error': 'Authentication required'}
    
    try:
        system_health = get_system_health()
        database_health = get_database_health()
        
        return {
            'system_health': system_health,
            'database_health': database_health,
            'size': size,
            'is_staff': request.user.is_staff,
            'user': request.user,
        }
    except Exception as e:
        return {'error': str(e)}

@register.inclusion_tag('monitoring/widgets/performance_metrics.html', takes_context=True)
def performance_metrics_widget(context, show_details=False):
    """Widget de métricas de performance"""
    request = context.get('request')
    
    if not request or not request.user.is_authenticated:
        return {'error': 'Authentication required'}
    
    try:
        system_health = get_system_health()
        data = system_health.get('data', {})
        
        return {
            'cpu_percent': data.get('cpu_percent', 0),
            'memory_percent': data.get('memory_percent', 0),
            'disk_percent': data.get('disk_percent', 0),
            'memory_available_gb': data.get('memory_available_gb', 0),
            'disk_free_gb': data.get('disk_free_gb', 0),
            'show_details': show_details,
            'is_staff': request.user.is_staff,
        }
    except Exception as e:
        return {'error': str(e)}

@register.inclusion_tag('monitoring/widgets/background_jobs.html', takes_context=True)
def background_jobs_widget(context):
    """Widget de background jobs"""
    request = context.get('request')
    
    if not request or not request.user.is_staff:
        return {'error': 'Staff access required'}
    
    try:
        job_stats = get_job_stats()
        
        return {
            'job_stats': job_stats,
            'is_staff': request.user.is_staff,
        }
    except Exception as e:
        return {'error': str(e)}

@register.inclusion_tag('monitoring/widgets/alerts.html', takes_context=True)
def alerts_widget(context, max_alerts=5):
    """Widget de alertas"""
    request = context.get('request')
    
    if not request or not request.user.is_authenticated:
        return {'error': 'Authentication required'}
    
    try:
        system_health = get_system_health()
        alerts = system_health.get('alerts', [])
        
        # Limita o número de alertas
        if max_alerts:
            alerts = alerts[:max_alerts]
        
        return {
            'alerts': alerts,
            'total_alerts': len(system_health.get('alerts', [])),
            'max_alerts': max_alerts,
            'is_staff': request.user.is_staff,
        }
    except Exception as e:
        return {'error': str(e)}

@register.inclusion_tag('monitoring/widgets/system_status_compact.html')
def system_status_widget_compact():
    """Widget compacto de status do sistema"""
    try:
        # Obter dados do sistema
        system_data = cache.get('system_monitoring_data', {})
        
        return {
            'system_cpu': system_data.get('cpu_percent', 0),
            'system_memory': system_data.get('memory_percent', 0),
            'system_disk': system_data.get('disk_percent', 0),
            'system_status': system_data.get('status', 'unknown'),
            'last_update': system_data.get('last_update', timezone.now())
        }
    except Exception as e:
        return {'error': str(e)}

@register.inclusion_tag('monitoring/widgets/performance_metrics_compact.html')
def performance_metrics_widget_compact():
    """Widget compacto de métricas de performance"""
    try:
        # Obter dados de performance
        perf_data = cache.get('performance_metrics_data', {})
        
        return {
            'avg_response_time': perf_data.get('avg_response_time', 0),
            'cache_hit_rate': perf_data.get('cache_hit_rate', 0),
            'db_queries': perf_data.get('db_queries', 0),
            'error_rate': perf_data.get('error_rate', 0),
            'last_update': perf_data.get('last_update', timezone.now())
        }
    except Exception as e:
        return {'error': str(e)}

@register.inclusion_tag('monitoring/widgets/background_jobs_compact.html')
def background_jobs_widget_compact():
    """Widget compacto de background jobs"""
    try:
        # Obter dados de jobs
        jobs_data = cache.get('background_jobs_data', {})
        
        return {
            'active_jobs': jobs_data.get('active_jobs', 0),
            'queued_jobs': jobs_data.get('queued_jobs', 0),
            'completed_jobs': jobs_data.get('completed_jobs', 0),
            'failed_jobs': jobs_data.get('failed_jobs', 0),
            'last_update': jobs_data.get('last_update', timezone.now())
        }
    except Exception as e:
        return {'error': str(e)}

@register.inclusion_tag('monitoring/widgets/alerts_compact.html')
def alerts_widget_compact():
    """Widget compacto de alertas"""
    try:
        # Obter dados de alertas
        alerts_data = cache.get('alerts_data', {})
        
        return {
            'critical_alerts': alerts_data.get('critical_alerts', 0),
            'warning_alerts': alerts_data.get('warning_alerts', 0),
            'total_alerts': alerts_data.get('total_alerts', 0),
            'recent_alerts': alerts_data.get('recent_alerts', []),
            'last_update': alerts_data.get('last_update', timezone.now())
        }
    except Exception as e:
        return {'error': str(e)}

@register.simple_tag
def monitoring_js_config():
    """Configuração JavaScript para monitoramento"""
    config = {
        'refresh_interval': 30000,  # 30 segundos
        'api_endpoints': {
            'system_health': '/monitoring/api/health/',
            'job_stats': '/monitoring/api/jobs/',
            'alerts': '/monitoring/api/alerts/',
        },
        'chart_colors': {
            'cpu': '#3b82f6',
            'memory': '#ef4444',
            'disk': '#f59e0b',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#ef4444',
        }
    }
    return mark_safe(f'window.MONITORING_CONFIG = {json.dumps(config)};')

@register.filter
def status_class(status):
    """Converte status para classe CSS"""
    status_map = {
        'healthy': 'text-green-600',
        'warning': 'text-yellow-600',
        'error': 'text-red-600',
        'critical': 'text-red-800',
        'unknown': 'text-gray-600',
    }
    return status_map.get(status, 'text-gray-600')

@register.filter
def status_icon(status):
    """Converte status para ícone"""
    icon_map = {
        'healthy': 'fas fa-check-circle',
        'warning': 'fas fa-exclamation-triangle',
        'error': 'fas fa-times-circle',
        'critical': 'fas fa-exclamation-circle',
        'unknown': 'fas fa-question-circle',
    }
    return icon_map.get(status, 'fas fa-question-circle')

@register.filter
def percentage_bar_color(percentage):
    """Cor da barra de progresso baseada na porcentagem"""
    if percentage >= 90:
        return 'bg-red-500'
    elif percentage >= 80:
        return 'bg-yellow-500'
    elif percentage >= 60:
        return 'bg-blue-500'
    else:
        return 'bg-green-500'
