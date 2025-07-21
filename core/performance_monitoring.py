"""
Performance monitoring and optimization tools for MoveMarias
"""
import time
import functools
import logging
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import View
import psutil
import json
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """System performance monitoring"""
    
    @staticmethod
    def get_system_metrics():
        """Get current system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used / (1024 * 1024)  # MB
            memory_total = memory.total / (1024 * 1024)  # MB
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used / (1024 * 1024 * 1024)  # GB
            disk_total = disk.total / (1024 * 1024 * 1024)  # GB
            
            # Network I/O
            network = psutil.net_io_counters()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'percent': memory_percent,
                    'used_mb': round(memory_used, 2),
                    'total_mb': round(memory_total, 2)
                },
                'disk': {
                    'percent': disk_percent,
                    'used_gb': round(disk_used, 2),
                    'total_gb': round(disk_total, 2)
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return None
    
    @staticmethod
    def get_django_metrics():
        """Get Django-specific metrics"""
        try:
            # Database queries
            queries = connection.queries
            query_count = len(queries)
            
            # Cache statistics
            cache_stats = {}
            try:
                cache_stats = {
                    'hits': cache._cache.get_stats()[0][1].get('hits', 0),
                    'misses': cache._cache.get_stats()[0][1].get('misses', 0),
                    'keys': cache._cache.get_stats()[0][1].get('curr_items', 0)
                }
            except:
                pass
            
            # Response time tracking
            response_times = cache.get('response_times', [])
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'database': {
                    'query_count': query_count,
                    'slow_queries': len([q for q in queries if float(q['time']) > 0.1])
                },
                'cache': cache_stats,
                'response_time': {
                    'average_ms': round(avg_response_time * 1000, 2),
                    'samples': len(response_times)
                }
            }
        except Exception as e:
            logger.error(f"Error getting Django metrics: {e}")
            return None
    
    @staticmethod
    def log_performance_metrics():
        """Log performance metrics to file"""
        system_metrics = PerformanceMonitor.get_system_metrics()
        django_metrics = PerformanceMonitor.get_django_metrics()
        
        if system_metrics and django_metrics:
            metrics = {
                'system': system_metrics,
                'django': django_metrics
            }
            
            logger.info(f"Performance metrics: {json.dumps(metrics)}")
            
            # Store in cache for dashboard
            cache.set('performance_metrics', metrics, 300)  # 5 minutes
            
            return metrics
        
        return None


class DatabaseOptimizer:
    """Database optimization utilities"""
    
    @staticmethod
    def analyze_slow_queries():
        """Analyze slow database queries"""
        slow_queries = []
        
        for query in connection.queries:
            if float(query['time']) > 0.1:  # Queries taking more than 100ms
                slow_queries.append({
                    'sql': query['sql'],
                    'time': float(query['time']),
                    'stack': query.get('stack', [])
                })
        
        return sorted(slow_queries, key=lambda x: x['time'], reverse=True)
    
    @staticmethod
    def get_query_statistics():
        """Get query statistics"""
        queries = connection.queries
        
        if not queries:
            return None
        
        total_time = sum(float(q['time']) for q in queries)
        query_count = len(queries)
        avg_time = total_time / query_count if query_count > 0 else 0
        
        return {
            'total_queries': query_count,
            'total_time': round(total_time, 4),
            'average_time': round(avg_time, 4),
            'slow_queries': len([q for q in queries if float(q['time']) > 0.1])
        }


class CacheOptimizer:
    """Cache optimization utilities"""
    
    @staticmethod
    def get_cache_statistics():
        """Get cache usage statistics"""
        try:
            # Get cache stats if available
            if hasattr(cache, '_cache') and hasattr(cache._cache, 'get_stats'):
                stats = cache._cache.get_stats()
                if stats:
                    return stats[0][1]
            return None
        except:
            return None
    
    @staticmethod
    def optimize_cache_keys():
        """Optimize cache key usage"""
        # This would implement cache key optimization logic
        pass
    
    @staticmethod
    def clear_expired_cache():
        """Clear expired cache entries"""
        try:
            cache.clear()
            return True
        except:
            return False


def performance_monitor(func):
    """Decorator to monitor function performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = e
            success = False
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Log performance data
        logger.info(f"Function {func.__name__} executed in {execution_time:.4f}s (success: {success})")
        
        # Store response time for monitoring
        response_times = cache.get('response_times', [])
        response_times.append(execution_time)
        
        # Keep only last 100 measurements
        if len(response_times) > 100:
            response_times = response_times[-100:]
        
        cache.set('response_times', response_times, 3600)  # 1 hour
        
        if not success:
            raise result
        
        return result
    
    return wrapper


def query_debugger(func):
    """Decorator to debug database queries"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if settings.DEBUG:
            initial_queries = len(connection.queries)
            
            result = func(*args, **kwargs)
            
            final_queries = len(connection.queries)
            query_count = final_queries - initial_queries
            
            if query_count > 10:  # Warn about excessive queries
                logger.warning(f"Function {func.__name__} executed {query_count} queries")
                
                # Log slow queries
                slow_queries = DatabaseOptimizer.analyze_slow_queries()
                if slow_queries:
                    logger.warning(f"Slow queries detected: {len(slow_queries)}")
            
            return result
        else:
            return func(*args, **kwargs)
    
    return wrapper


@method_decorator(staff_member_required, name='dispatch')
class PerformanceMonitoringView(View):
    """View for performance monitoring dashboard"""
    
    def get(self, request):
        """Get performance monitoring data"""
        # Get cached metrics
        cached_metrics = cache.get('performance_metrics')
        
        if not cached_metrics:
            # Generate fresh metrics
            cached_metrics = PerformanceMonitor.log_performance_metrics()
        
        # Get database stats
        db_stats = DatabaseOptimizer.get_query_statistics()
        
        # Get cache stats
        cache_stats = CacheOptimizer.get_cache_statistics()
        
        data = {
            'metrics': cached_metrics,
            'database': db_stats,
            'cache': cache_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        return JsonResponse(data)


@require_http_methods(["POST"])
@staff_member_required
def optimize_performance(request):
    """Optimize system performance"""
    try:
        # Clear expired cache
        cache_cleared = CacheOptimizer.clear_expired_cache()
        
        # Log current metrics
        metrics = PerformanceMonitor.log_performance_metrics()
        
        return JsonResponse({
            'success': True,
            'cache_cleared': cache_cleared,
            'metrics': metrics
        })
    
    except Exception as e:
        logger.error(f"Error optimizing performance: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@staff_member_required
def slow_queries_report(request):
    """Get slow queries report"""
    try:
        slow_queries = DatabaseOptimizer.analyze_slow_queries()
        
        return JsonResponse({
            'slow_queries': slow_queries,
            'count': len(slow_queries),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error generating slow queries report: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


class PerformanceMiddleware:
    """Middleware to monitor request performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        end_time = time.time()
        request_time = end_time - start_time
        
        # Log slow requests
        if request_time > 1.0:  # Requests taking more than 1 second
            logger.warning(f"Slow request: {request.path} took {request_time:.2f}s")
        
        # Add performance header
        response['X-Response-Time'] = f"{request_time:.4f}s"
        
        return response


# Performance monitoring utilities
def get_performance_summary():
    """Get performance summary for dashboard"""
    try:
        system_metrics = PerformanceMonitor.get_system_metrics()
        django_metrics = PerformanceMonitor.get_django_metrics()
        
        return {
            'system': system_metrics,
            'django': django_metrics,
            'health_score': calculate_health_score(system_metrics, django_metrics)
        }
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        return None


def calculate_health_score(system_metrics, django_metrics):
    """Calculate system health score (0-100)"""
    try:
        score = 100
        
        # CPU penalty
        if system_metrics['cpu']['percent'] > 80:
            score -= 20
        elif system_metrics['cpu']['percent'] > 60:
            score -= 10
        
        # Memory penalty
        if system_metrics['memory']['percent'] > 80:
            score -= 20
        elif system_metrics['memory']['percent'] > 60:
            score -= 10
        
        # Disk penalty
        if system_metrics['disk']['percent'] > 90:
            score -= 15
        elif system_metrics['disk']['percent'] > 80:
            score -= 10
        
        # Database penalty
        if django_metrics['database']['slow_queries'] > 10:
            score -= 15
        elif django_metrics['database']['slow_queries'] > 5:
            score -= 10
        
        return max(0, score)
    except:
        return 50  # Default score if calculation fails
