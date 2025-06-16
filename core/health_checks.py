"""
Health check functions for Move Marias system
"""
import redis
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import logging

# Optional Celery import
try:
    from celery import current_app
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

logger = logging.getLogger(__name__)

def redis_check():
    """Check Redis connection and functionality"""
    try:
        # Test basic cache operations
        test_key = 'health_check_redis'
        test_value = 'ok'
        
        cache.set(test_key, test_value, 30)
        retrieved_value = cache.get(test_key)
        
        if retrieved_value != test_value:
            return False, "Redis cache not responding correctly"
        
        # Clean up test key
        cache.delete(test_key)
        
        return True, "Redis is healthy"
        
    except Exception as e:
        return False, f"Redis check failed: {str(e)}"

def celery_check():
    """Check Celery worker availability"""
    try:
        # Check if Celery is available
        if not CELERY_AVAILABLE:
            return False, "Celery not installed"
        
        # Check if Celery is configured
        if not hasattr(settings, 'CELERY_BROKER_URL'):
            return False, "Celery not configured"
        
        # Get active workers
        celery_app = current_app
        inspect = celery_app.control.inspect()
        
        # Check if any workers are active
        active_workers = inspect.active()
        
        if not active_workers:
            return False, "No active Celery workers found"
        
        worker_count = sum(len(tasks) for tasks in active_workers.values())
        
        return True, f"Celery is healthy with {len(active_workers)} workers"
        
    except Exception as e:
        return False, f"Celery check failed: {str(e)}"

def database_check():
    """Check database connection"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        if result and result[0] == 1:
            return True, "Database is healthy"
        else:
            return False, "Database query returned unexpected result"
            
    except Exception as e:
        return False, f"Database check failed: {str(e)}"

def disk_space_check(min_free_gb=1.0):
    """Check available disk space"""
    try:
        import shutil
        
        total, used, free = shutil.disk_usage('/')
        free_gb = free / (1024 ** 3)  # Convert to GB
        
        if free_gb < min_free_gb:
            return False, f"Low disk space: {free_gb:.2f}GB free (minimum: {min_free_gb}GB)"
        
        return True, f"Disk space is healthy: {free_gb:.2f}GB free"
        
    except Exception as e:
        return False, f"Disk space check failed: {str(e)}"

def memory_check(max_usage_percent=90):
    """Check memory usage"""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        usage_percent = memory.percent
        
        if usage_percent > max_usage_percent:
            return False, f"High memory usage: {usage_percent:.1f}% (maximum: {max_usage_percent}%)"
        
        return True, f"Memory usage is healthy: {usage_percent:.1f}%"
        
    except ImportError:
        return True, "Memory check skipped (psutil not available)"
    except Exception as e:
        return False, f"Memory check failed: {str(e)}"

def run_all_health_checks():
    """Run all health checks and return results"""
    checks = {
        'database': database_check,
        'redis': redis_check,
        'celery': celery_check,
        'disk_space': disk_space_check,
        'memory': memory_check,
    }
    
    results = {}
    overall_healthy = True
    
    for check_name, check_func in checks.items():
        try:
            is_healthy, message = check_func()
            results[check_name] = {
                'healthy': is_healthy,
                'message': message,
            }
            
            if not is_healthy:
                overall_healthy = False
                logger.warning(f"Health check failed - {check_name}: {message}")
            else:
                logger.info(f"Health check passed - {check_name}: {message}")
                
        except Exception as e:
            results[check_name] = {
                'healthy': False,
                'message': f"Check failed with exception: {str(e)}",
            }
            overall_healthy = False
            logger.error(f"Health check exception - {check_name}: {str(e)}")
    
    results['overall'] = {
        'healthy': overall_healthy,
        'message': "All checks passed" if overall_healthy else "Some checks failed",
    }
    
    return results
