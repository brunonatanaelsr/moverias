# Health check and monitoring views for Move Marias
import time
import json
import psutil
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import logging

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
            'python_version': f"{psutil.version_info[0]}.{psutil.version_info[1]}.{psutil.version_info[2]}"
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
