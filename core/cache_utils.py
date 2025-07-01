"""
Cache decorators and utilities for Move Marias system.
"""

from functools import wraps
from django.core.cache import cache
from django.conf import settings
import hashlib
import json


def cache_view(timeout=300, key_prefix='view', vary_on_user=True, vary_on_params=None):
    """
    Decorator to cache view results.
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key
        vary_on_user: Include user ID in cache key
        vary_on_params: List of GET parameters to include in cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Build cache key
            key_parts = [key_prefix, request.path]
            
            # Include user in cache key if requested
            if vary_on_user and hasattr(request, 'user') and request.user.is_authenticated:
                key_parts.append(f'user_{request.user.id}')
            
            # Include specific GET parameters
            if vary_on_params:
                params = {k: request.GET.get(k, '') for k in vary_on_params if k in request.GET}
                if params:
                    params_str = json.dumps(params, sort_keys=True)
                    key_parts.append(hashlib.md5(params_str.encode()).hexdigest()[:8])
            
            # Include all GET parameters hash
            if request.GET:
                get_hash = hashlib.md5(str(sorted(request.GET.items())).encode()).hexdigest()[:8]
                key_parts.append(get_hash)
            
            cache_key = '_'.join(key_parts)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Generate result and cache it
            result = func(request, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator


def cache_model_method(timeout=300, key_prefix='model'):
    """
    Decorator to cache model method results.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Build cache key including model class and instance pk
            model_name = self.__class__.__name__
            instance_id = getattr(self, 'pk', 'no_pk')
            args_hash = hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()[:8]
            
            cache_key = f"{key_prefix}_{model_name}_{instance_id}_{func.__name__}_{args_hash}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Generate result and cache it
            result = func(self, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern):
    """
    Invalidate all cache keys matching a pattern.
    """
    from django.core.cache.backends.base import InvalidCacheKey
    
    try:
        # This works with Redis backend
        from django.core.cache.backends.redis import RedisCache
        if isinstance(cache, RedisCache):
            keys = cache._cache.keys(pattern)
            if keys:
                cache.delete_many([key.decode() if isinstance(key, bytes) else key for key in keys])
    except (ImportError, AttributeError):
        # Fallback for other cache backends
        pass


class CacheInvalidator:
    """
    Helper class to manage cache invalidation.
    """
    
    @staticmethod
    def invalidate_beneficiary_cache(beneficiary_id):
        """Invalidate all cache related to a specific beneficiary."""
        patterns = [
            f'view_*beneficiary*{beneficiary_id}*',
            f'model_Beneficiary_{beneficiary_id}_*',
            'view_*/members/*',
            'view_*/dashboard/*',
        ]
        
        for pattern in patterns:
            invalidate_cache_pattern(pattern)
    
    @staticmethod
    def invalidate_dashboard_cache():
        """Invalidate dashboard-related cache."""
        patterns = [
            'view_*/dashboard/*',
            'view_dashboard_*',
        ]
        
        for pattern in patterns:
            invalidate_cache_pattern(pattern)
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate user-specific cache."""
        patterns = [
            f'view_*user_{user_id}*',
            f'model_CustomUser_{user_id}_*',
        ]
        
        for pattern in patterns:
            invalidate_cache_pattern(pattern)


# Cache timeout constants
CACHE_TIMEOUTS = {
    'SHORT': 60,      # 1 minute
    'MEDIUM': 300,    # 5 minutes
    'LONG': 900,      # 15 minutes
    'VERY_LONG': 3600, # 1 hour
}
