import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger('movemarias')

class PerformanceMiddleware(MiddlewareMixin):
    """Monitor performance and log slow requests"""
    
    def process_request(self, request):
        request._start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log slow requests
            if duration > getattr(settings, 'SLOW_REQUEST_THRESHOLD', 2.0):
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s for user {getattr(request.user, 'email', 'anonymous')}"
                )
            
            # Add performance header in debug mode
            if settings.DEBUG:
                response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response

class SecurityMiddleware(MiddlewareMixin):
    """Enhanced security middleware"""
    
    def process_request(self, request):
        # Log suspicious activities
        if self._is_suspicious_request(request):
            logger.warning(
                f"Suspicious request from {self._get_client_ip(request)}: "
                f"{request.method} {request.path}"
            )
    
    def _is_suspicious_request(self, request):
        """Detect potentially suspicious requests"""
        suspicious_patterns = [
            'admin', 'wp-admin', 'phpMyAdmin', '.env', 'config',
        ]
        
        path_lower = request.path.lower()
        return any(pattern in path_lower for pattern in suspicious_patterns)
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class AuditMiddleware(MiddlewareMixin):
    """Audit trail middleware for tracking user actions"""
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Only log authenticated users' actions
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                logger.info(
                    f"User action: {request.user.email} performed {request.method} "
                    f"on {request.path} from {self._get_client_ip(request)}"
                )
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
