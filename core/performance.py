"""
Performance optimization utilities for Move Marias
"""
import functools
import time
from django.core.cache import cache
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
import logging

logger = logging.getLogger('movemarias')

def cached_property_with_timeout(timeout=300):
    """
    Decorator for caching property results with timeout
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self):
            cache_key = f"{self.__class__.__name__}_{func.__name__}_{id(self)}"
            result = cache.get(cache_key)
            if result is None:
                result = func(self)
                cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

def cache_page_if_anonymous(timeout=300):
    """
    Cache page only for anonymous users
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_anonymous:
                cache_key = f"page_cache_{request.path}_{request.GET.urlencode()}"
                cached_response = cache.get(cache_key)
                if cached_response:
                    return cached_response
                
                response = view_func(request, *args, **kwargs)
                if response.status_code == 200:
                    cache.set(cache_key, response, timeout)
                return response
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def measure_db_queries(view_func):
    """
    Decorator to measure database queries in development
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if settings.DEBUG:
            initial_queries = len(connection.queries)
            start_time = time.time()
            
            response = view_func(request, *args, **kwargs)
            
            end_time = time.time()
            query_count = len(connection.queries) - initial_queries
            duration = end_time - start_time
            
            if query_count > 10 or duration > 1.0:
                logger.warning(
                    f"Performance warning: {request.path} executed {query_count} "
                    f"queries in {duration:.2f}s"
                )
            
            return response
        return view_func(request, *args, **kwargs)
    return wrapper

class QueryOptimizer:
    """
    Helper class for query optimization
    """
    
    @staticmethod
    def optimize_beneficiary_queries():
        """
        Common query patterns for beneficiaries
        """
        from members.models import Beneficiary
        
        return {
            'list_with_counts': Beneficiary.objects.select_related().prefetch_related(
                'project_enrollments',
                'social_assistances',
                'evolutions'
            ).annotate(
                project_count=models.Count('project_enrollments'),
                assistance_count=models.Count('social_assistances')
            ),
            
            'basic_list': Beneficiary.objects.only(
                'id', 'full_name', 'dob', 'neighbourhood', 'phone_1', 'created_at'
            )
        }
    
    @staticmethod
    def batch_update_helper(model_class, updates, batch_size=100):
        """
        Helper for batch updates
        """
        objects_to_update = []
        for obj_id, update_data in updates.items():
            obj = model_class(id=obj_id, **update_data)
            objects_to_update.append(obj)
            
            if len(objects_to_update) >= batch_size:
                model_class.objects.bulk_update(
                    objects_to_update, 
                    list(update_data.keys())
                )
                objects_to_update = []
        
        # Update remaining objects
        if objects_to_update:
            model_class.objects.bulk_update(
                objects_to_update, 
                list(updates[list(updates.keys())[0]].keys())
            )

def optimize_images(image_field, sizes=None):
    """
    Optimize and resize images
    """
    if sizes is None:
        sizes = [(150, 150), (300, 300), (600, 600)]
    
    # This would integrate with Pillow for image optimization
    # Implementation depends on your image handling needs
    pass

class CacheManager:
    """
    Centralized cache management
    """
    
    TIMEOUTS = {
        'short': 300,      # 5 minutes
        'medium': 1800,    # 30 minutes
        'long': 3600,      # 1 hour
        'very_long': 86400 # 24 hours
    }
    
    @classmethod
    def invalidate_user_cache(cls, user_id):
        """Invalidate all cache keys for a specific user"""
        patterns = [
            f"user_{user_id}_*",
            f"beneficiaries_user_{user_id}_*",
            f"dashboard_user_{user_id}_*"
        ]
        
        # This would require django-redis or similar
        # for pattern-based cache deletion
        pass
    
    @classmethod
    def warm_cache_for_user(cls, user):
        """Pre-warm cache with commonly accessed data"""
        if hasattr(user, 'groups'):
            # Cache user permissions
            cache.set(f"user_permissions_{user.id}", 
                     list(user.get_all_permissions()), 
                     cls.TIMEOUTS['long'])
    
    @classmethod
    def get_or_set_with_lock(cls, key, callable_func, timeout=None):
        """
        Get or set cache with distributed lock to prevent cache stampede
        """
        lock_key = f"lock_{key}"
        if cache.add(lock_key, "locked", 30):  # 30 second lock
            try:
                result = callable_func()
                cache.set(key, result, timeout or cls.TIMEOUTS['medium'])
                return result
            finally:
                cache.delete(lock_key)
        else:
            # Wait for lock to be released and try to get cached value
            time.sleep(0.1)
            return cache.get(key)

# Database connection pooling helper
def get_db_pool_status():
    """
    Get database connection pool status for monitoring
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return {
                'status': 'healthy',
                'queries_count': len(connection.queries) if settings.DEBUG else 'N/A'
            }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }
