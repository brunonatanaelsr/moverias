# Health check and monitoring views for Move Marias
import time
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from core.monitoring import get_system_health, get_database_health, get_full_system_status
from core.reporting import generate_security_report, generate_performance_report
from core.health_checks import run_all_health_checks
import logging

# Optional psutil import
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger('movemarias')

@never_cache
@require_http_methods(["GET"])
def health_check(request):
    """Basic health check endpoint"""
    return HttpResponse("OK", content_type="text/plain")

@never_cache
@require_http_methods(["GET"])
def health_detailed(request):
    """Detailed health check with system information"""
    start_time = time.time()
    
    health_data = {
        'status': 'healthy',
        'timestamp': time.time(),
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_data['checks']['database'] = {'status': 'healthy', 'response_time': 0}
    except Exception as e:
        health_data['checks']['database'] = {'status': 'unhealthy', 'error': str(e)}
        health_data['status'] = 'unhealthy'
    
    # Cache check
    try:
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test', 30)
        cache_value = cache.get(cache_key)
        if cache_value == 'test':
            health_data['checks']['cache'] = {'status': 'healthy'}
        else:
            health_data['checks']['cache'] = {'status': 'unhealthy', 'error': 'Cache test failed'}
            health_data['status'] = 'degraded'
    except Exception as e:
        health_data['checks']['cache'] = {'status': 'unhealthy', 'error': str(e)}
        health_data['status'] = 'degraded'
    
    # System resources
    try:
        if PSUTIL_AVAILABLE:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_data['checks']['system'] = {
                'status': 'healthy',
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'cpu_percent': psutil.cpu_percent(interval=1)
            }
            
            # Alert if resources are high
            if memory.percent > 90 or disk.percent > 90:
                health_data['status'] = 'degraded'
        else:
            health_data['checks']['system'] = {
                'status': 'unknown',
                'error': 'psutil not available'
            }
            
    except Exception as e:
        health_data['checks']['system'] = {'status': 'unknown', 'error': str(e)}
    
    # Response time
    health_data['response_time'] = time.time() - start_time
    
    status_code = 200
    if health_data['status'] == 'unhealthy':
        status_code = 503
    elif health_data['status'] == 'degraded':
        status_code = 200  # Still functional
    
    return JsonResponse(health_data, status=status_code)

@never_cache
@require_http_methods(["GET"])
def metrics(request):
    """Prometheus-style metrics endpoint"""
    try:
        if not PSUTIL_AVAILABLE:
            return JsonResponse({'error': 'psutil not available'}, status=503)
            
        # System metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Database metrics
        db_connections = 0
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT count(*) 
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """)
                db_connections = cursor.fetchone()[0]
        except:
            pass
        
        metrics_data = {
            'system_memory_percent': memory.percent,
            'system_memory_available_bytes': memory.available,
            'system_disk_percent': disk.percent,
            'system_disk_free_bytes': disk.free,
            'system_cpu_percent': cpu_percent,
            'database_connections_active': db_connections,
            'django_version': settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else 'unknown',
            'python_version': f"{psutil.version_info[0]}.{psutil.version_info[1]}.{psutil.version_info[2]}" if PSUTIL_AVAILABLE else 'unknown'
        }
        
        return JsonResponse(metrics_data)
        
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return JsonResponse({'error': 'Failed to generate metrics'}, status=500)

@never_cache
@require_http_methods(["GET"])
def status(request):
    """Simple status page for monitoring"""
    return JsonResponse({
        'status': 'operational',
        'version': '1.0.0',
        'environment': getattr(settings, 'ENVIRONMENT', 'unknown'),
        'debug': settings.DEBUG
    })

class PerformanceMiddleware:
    """Middleware to track request performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.performance_logger = logging.getLogger('movemarias.performance')
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log slow requests
        if duration > 2.0:  # Requests taking more than 2 seconds
            self.performance_logger.warning(
                f"Slow request: {request.method} {request.path} "
                f"took {duration:.2f}s (User: {getattr(request.user, 'username', 'anonymous')})"
            )
        
        # Add performance header
        response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response

class SecurityMiddleware:
    """Enhanced security middleware with logging"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_logger = logging.getLogger('movemarias.security')
    
    def __call__(self, request):
        # Log suspicious patterns
        suspicious_patterns = [
            '.php', '.asp', '.jsp', 'wp-admin', 'phpmyadmin',
            'eval(', 'base64_decode', 'shell_exec'
        ]
        
        request_path = request.path.lower()
        if any(pattern in request_path for pattern in suspicious_patterns):
            self.security_logger.warning(
                f"Suspicious request pattern detected: {request.path} "
                f"from {self.get_client_ip(request)}"
            )
        
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

@staff_member_required
def system_status(request):
    """System status dashboard"""
    try:
        status_data = get_full_system_status()
        health_checks = run_all_health_checks()
        
        context = {
            'system_status': status_data,
            'health_checks': health_checks,
            'page_title': 'System Status Dashboard'
        }
        
        return render(request, 'core/system_status.html', context)
        
    except Exception as e:
        context = {
            'error': str(e),
            'page_title': 'System Status Dashboard'
        }
        return render(request, 'core/system_status.html', context)

@staff_member_required
def system_status_api(request):
    """API endpoint for system status (AJAX)"""
    try:
        status_data = get_full_system_status()
        health_checks = run_all_health_checks()
        
        return JsonResponse({
            'success': True,
            'system_status': status_data,
            'health_checks': health_checks,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@staff_member_required
def security_report_view(request):
    """Security report view"""
    try:
        if request.method == 'POST':
            # Generate new report
            report_path, report_data = generate_security_report()
            
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'success': True,
                    'report_data': report_data,
                    'report_path': str(report_path)
                })
            
            context = {
                'report_data': report_data,
                'report_generated': True,
                'page_title': 'Security Report'
            }
            
        else:
            context = {
                'page_title': 'Security Report'
            }
        
        return render(request, 'core/security_report.html', context)
        
    except Exception as e:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        context = {
            'error': str(e),
            'page_title': 'Security Report'
        }
        return render(request, 'core/security_report.html', context)

@staff_member_required
def performance_report_view(request):
    """Performance report view"""
    try:
        if request.method == 'POST':
            # Generate new report
            report_path, report_data = generate_performance_report()
            
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'success': True,
                    'report_data': report_data,
                    'report_path': str(report_path)
                })
            
            context = {
                'report_data': report_data,
                'report_generated': True,
                'page_title': 'Performance Report'
            }
            
        else:
            context = {
                'page_title': 'Performance Report'
            }
        
        return render(request, 'core/performance_report.html', context)
        
    except Exception as e:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        context = {
            'error': str(e),
            'page_title': 'Performance Report'
        }
        return render(request, 'core/performance_report.html', context)

@staff_member_required
@never_cache
def system_monitoring_dashboard(request):
    """Dashboard de monitoramento do sistema"""
    try:
        # Obter métricas do sistema
        system_health = get_system_health()
        
        # Métricas básicas do sistema
        system_metrics = {}
        if PSUTIL_AVAILABLE:
            system_metrics = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'cpu_count': psutil.cpu_count(),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_used': f"{psutil.virtual_memory().used / (1024**3):.1f}GB",
                'memory_total': f"{psutil.virtual_memory().total / (1024**3):.1f}GB",
                'disk_percent': psutil.disk_usage('/').percent,
                'disk_used': f"{psutil.disk_usage('/').used / (1024**3):.1f}GB",
                'disk_total': f"{psutil.disk_usage('/').total / (1024**3):.1f}GB",
            }
        
        # Métricas do banco de dados
        db_metrics = {
            'active_connections': get_active_db_connections(),
            'slow_queries': cache.get('slow_queries_count', 0),
            'avg_query_time': cache.get('avg_query_time', 0),
        }
        
        # Métricas de cache
        cache_metrics = {
            'hit_rate': cache.get('cache_hit_rate', 0),
            'active_keys': cache.get('cache_keys_count', 0),
            'memory_usage': cache.get('cache_memory_usage', 'N/A'),
        }
        
        # Métricas de segurança
        security_metrics = {
            'login_attempts': cache.get('login_attempts_today', 0),
            'blocked_ips': cache.get('blocked_ips_count', 0),
            'security_score': cache.get('security_score', 9),
        }
        
        # Alertas recentes
        recent_alerts = cache.get('recent_alerts', [])
        
        context = {
            'system_health': system_health,
            'system_metrics': system_metrics,
            'db_metrics': db_metrics,
            'cache_metrics': cache_metrics,
            'security_metrics': security_metrics,
            'recent_alerts': recent_alerts[:10],  # Últimos 10 alertas
            'last_update': time.time(),
        }
        
        return render(request, 'core/system_monitoring.html', context)
        
    except Exception as e:
        logger.error(f"Erro no dashboard de monitoramento: {e}")
        return render(request, 'core/system_monitoring.html', {
            'error': 'Erro ao carregar dados de monitoramento',
            'system_health': {'status': 'error'},
            'system_metrics': {},
            'db_metrics': {},
            'cache_metrics': {},
            'security_metrics': {},
            'recent_alerts': [],
        })

def get_active_db_connections():
    """Obter número de conexões ativas do banco"""
    try:
        with connection.cursor() as cursor:
            if 'postgresql' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
            elif 'mysql' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("SHOW STATUS LIKE 'Threads_connected';")
            elif 'sqlite' in settings.DATABASES['default']['ENGINE']:
                # SQLite não tem conexões persistentes
                return 1
            else:
                return 0
            
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception:
        return 0

@staff_member_required
@require_http_methods(["POST"])
def refresh_monitoring(request):
    """Atualizar dados de monitoramento via HTMX"""
    try:
        # Limpar cache de métricas para forçar atualização
        cache.delete_many([
            'system_health',
            'cache_hit_rate',
            'cache_keys_count',
            'slow_queries_count',
            'avg_query_time'
        ])
        
        # Retornar dados atualizados
        return system_monitoring_dashboard(request)
        
    except Exception as e:
        logger.error(f"Erro ao atualizar monitoramento: {e}")
        return JsonResponse({'error': 'Erro ao atualizar dados'}, status=500)

@staff_member_required
@require_http_methods(["POST"])
def clear_cache(request):
    """Limpar cache do sistema"""
    try:
        cache.clear()
        logger.info("Cache limpo por requisição do usuário")
        
        return JsonResponse({
            'success': True,
            'message': 'Cache limpo com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        return JsonResponse({'error': 'Erro ao limpar cache'}, status=500)

@staff_member_required
def system_alerts(request):
    """Mostrar todos os alertas do sistema"""
    try:
        all_alerts = cache.get('all_system_alerts', [])
        
        context = {
            'alerts': all_alerts,
            'total_alerts': len(all_alerts),
        }
        
        return render(request, 'core/system_alerts_modal.html', context)
        
    except Exception as e:
        logger.error(f"Erro ao carregar alertas: {e}")
        return render(request, 'core/system_alerts_modal.html', {
            'error': 'Erro ao carregar alertas',
            'alerts': [],
            'total_alerts': 0,
        })

@staff_member_required
@require_http_methods(["GET"])
def export_alerts(request):
    """Exportar alertas para arquivo"""
    try:
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        all_alerts = cache.get('all_system_alerts', [])
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="alertas_sistema_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Data/Hora', 'Nível', 'Título', 'Mensagem', 'Detalhes'])
        
        for alert in all_alerts:
            writer.writerow([
                alert.get('timestamp', ''),
                alert.get('level', ''),
                alert.get('title', ''),
                alert.get('message', ''),
                alert.get('details', '')
            ])
        
        logger.info("Relatório de alertas exportado")
        return response
        
    except Exception as e:
        logger.error(f"Erro ao exportar alertas: {e}")
        return JsonResponse({'error': 'Erro ao exportar alertas'}, status=500)

@staff_member_required
@require_http_methods(["POST"])
def clear_alerts(request):
    """Limpar todos os alertas do sistema"""
    try:
        cache.delete('all_system_alerts')
        cache.delete('recent_alerts')
        
        logger.info("Alertas limpos por requisição do usuário")
        
        return JsonResponse({
            'success': True,
            'message': 'Alertas limpos com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao limpar alertas: {e}")
        return JsonResponse({'error': 'Erro ao limpar alertas'}, status=500)

@staff_member_required
@require_http_methods(["GET", "POST"])
def generate_report(request):
    """Gerar relatórios do sistema - Modal para HTMX"""
    try:
        if request.method == 'POST':
            # Process report generation request
            report_type = request.POST.get('report_type', 'system_health')
            
            # Import the Celery task
            from .tasks import generate_report as generate_report_task
            
            # Start the report generation task
            task_result = generate_report_task.delay(
                report_type=report_type,
                user_id=request.user.id,
                parameters={}
            )
            
            logger.info(f"Report generation task started: {task_result.id}")
            
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': True,
                    'message': f'Relatório "{report_type}" está sendo gerado. Você será notificado quando estiver pronto.',
                    'task_id': task_result.id
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': 'Relatório está sendo gerado',
                    'task_id': task_result.id
                })
        
        # GET request - show the modal form
        context = {
            'report_types': [
                ('system_health', 'Relatório de Saúde do Sistema'),
                ('member_activity', 'Relatório de Atividade dos Membros'),
                ('performance', 'Relatório de Performance'),
                ('security', 'Relatório de Segurança'),
            ]
        }
        
        return render(request, 'core/generate_report_modal.html', context)
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': False,
                'error': 'Erro ao gerar relatório'
            }, status=500)
        else:
            return JsonResponse({'error': 'Erro ao gerar relatório'}, status=500)
