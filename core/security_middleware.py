"""
Middleware de segurança personalizado para o Move Marias
"""
import logging
import time
from django.core.cache import cache
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware personalizado de segurança
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Processar request antes das views
        """
        # Rate limiting
        if self._is_rate_limited(request):
            logger.warning(f"Rate limit exceeded for IP: {self._get_client_ip(request)}")
            return JsonResponse({
                'error': 'Muitas tentativas. Tente novamente em alguns minutos.'
            }, status=429)
        
        # Validar headers suspeitos
        if self._has_suspicious_headers(request):
            logger.warning(f"Suspicious headers from IP: {self._get_client_ip(request)}")
            return HttpResponseForbidden("Request bloqueado por segurança")
        
        return None
    
    def process_response(self, request, response):
        """
        Adicionar headers de segurança
        """
        # Headers de segurança básicos
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Adicionar headers específicos se não for DEBUG
        if not getattr(settings, 'DEBUG', True):
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            response['Content-Security-Policy'] = self._get_csp_header()
        
        return response
    
    def _get_client_ip(self, request):
        """
        Obter IP real do cliente
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_rate_limited(self, request):
        """
        Verificar rate limiting
        """
        ip = self._get_client_ip(request)
        
        # Rate limits diferentes por tipo de endpoint
        if request.path.startswith('/api/'):
            return self._check_api_rate_limit(ip)
        elif request.path.startswith('/accounts/login/'):
            return self._check_login_rate_limit(ip)
        elif request.method == 'POST':
            return self._check_post_rate_limit(ip)
        
        return False
    
    def _check_api_rate_limit(self, ip):
        """
        Rate limit para API (60 requests por minuto)
        """
        cache_key = f'api_rate_limit_{ip}'
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= 60:
            return True
        
        cache.set(cache_key, current_requests + 1, 60)
        return False
    
    def _check_login_rate_limit(self, ip):
        """
        Rate limit para login (5 tentativas por 5 minutos)
        """
        cache_key = f'login_rate_limit_{ip}'
        current_attempts = cache.get(cache_key, 0)
        
        if current_attempts >= 5:
            return True
        
        cache.set(cache_key, current_attempts + 1, 300)
        return False
    
    def _check_post_rate_limit(self, ip):
        """
        Rate limit para POSTs em geral (30 por minuto)
        """
        cache_key = f'post_rate_limit_{ip}'
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= 30:
            return True
        
        cache.set(cache_key, current_requests + 1, 60)
        return False
    
    def _has_suspicious_headers(self, request):
        """
        Detectar headers suspeitos
        """
        # Permitir em modo DEBUG ou durante testes
        if settings.DEBUG or hasattr(request, '_test_mode'):
            return False
            
        suspicious_patterns = [
            'sqlmap',
            'nmap',
            'nikto',
            'wget',
            'curl',
            'python-requests',
            '<script>',
            'javascript:',
            'data:text/html',
        ]
        
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        for pattern in suspicious_patterns:
            if pattern in user_agent:
                return True
        
        # Verificar se User-Agent está vazio (suspeito) - apenas em produção
        if not settings.DEBUG and not request.META.get('HTTP_USER_AGENT', '').strip():
            return True
        
        return False
    
    def _get_csp_header(self):
        """
        Gerar header Content Security Policy
        """
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "img-src 'self' data: https:",
            "font-src 'self' https://cdn.jsdelivr.net",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        
        return "; ".join(csp_directives)


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware para auditoria de ações importantes
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Auditar views importantes
        """
        # Registrar ações importantes
        important_paths = [
            '/dashboard/beneficiary/create/',
            '/dashboard/beneficiary/update/',
            '/social/anamnesis/create/',
            '/users/create/',
            '/admin/',
        ]
        
        if any(request.path.startswith(path) for path in important_paths):
            self._log_important_action(request, view_func)
        
        return None
    
    def _log_important_action(self, request, view_func):
        """
        Registrar ação importante
        """
        user = request.user if not isinstance(request.user, AnonymousUser) else 'Anonymous'
        
        log_data = {
            'user': str(user),
            'ip': self._get_client_ip(request),
            'path': request.path,
            'method': request.method,
            'view': f"{view_func.__module__}.{view_func.__name__}",
            'timestamp': time.time(),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')
        }
        
        logger.info(f"Important action: {log_data}")
        
        # Salvar em cache para análise posterior
        cache_key = f'audit_log_{int(time.time())}'
        cache.set(cache_key, log_data, 86400)  # 24 horas
    
    def _get_client_ip(self, request):
        """
        Obter IP real do cliente
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware para monitoramento de performance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Marcar início do request
        """
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """
        Calcular tempo de resposta
        """
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log requests lentos
            if duration > 2.0:  # Mais de 2 segundos
                logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
            
            # Adicionar header de timing
            response['X-Response-Time'] = f"{duration:.3f}s"
            
            # Salvar métricas em cache para análise
            if duration > 1.0:  # Salvar requests > 1s
                cache_key = f'slow_request_{int(time.time())}'
                cache.set(cache_key, {
                    'path': request.path,
                    'method': request.method,
                    'duration': duration,
                    'user': str(request.user) if hasattr(request, 'user') else 'Unknown'
                }, 3600)
        
        return response
