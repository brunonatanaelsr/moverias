import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse

logger = logging.getLogger('movemarias')


class ErrorLoggingMiddleware(MiddlewareMixin):
    """
    Middleware para capturar e logar erros 500+ automaticamente.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        
        # Log errors 500+
        if response.status_code >= 500:
            duration = time.time() - start_time
            logger.error(
                f'Server Error {response.status_code} for {request.method} {request.path} '
                f'- Duration: {duration:.2f}s - User: {getattr(request, "user", "Anonymous")} '
                f'- IP: {self._get_client_ip(request)}'
            )
        
        # Log slow requests (>2s)
        elif time.time() - start_time > 2:
            duration = time.time() - start_time
            logger.warning(
                f'Slow Request: {request.method} {request.path} '
                f'- Duration: {duration:.2f}s - Status: {response.status_code}'
            )
        
        return response
    
    def process_exception(self, request, exception):
        """
        Captura exceções não tratadas.
        """
        logger.error(
            f'Unhandled Exception for {request.method} {request.path}: {str(exception)}',
            exc_info=True,
            extra={
                'request_path': request.path,
                'request_method': request.method,
                'user': str(getattr(request, 'user', 'Anonymous')),
                'ip_address': self._get_client_ip(request),
            }
        )
        
        # Em desenvolvimento, deixa o Django mostrar a página de erro
        if settings.DEBUG:
            return None
        
        # Em produção, retorna uma resposta JSON amigável para AJAX
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Ocorreu um erro interno. Nossa equipe foi notificada.',
                'status': 'error'
            }, status=500)
        
        return None
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


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

class SecurityHeadersMiddleware:
    """
    Middleware customizado para headers de segurança adicionais
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), '
            'usb=(), payment=(), accelerometer=(), gyroscope=()'
        )
        
        # Remove server identification
        if 'Server' in response:
            del response['Server']
        
        # Security logging
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Log security-relevant actions
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                logger = logging.getLogger('security')
                logger.info(f"Security action: {request.method} {request.path} by {request.user.email}")
        
        return response


"""
Middleware para adicionar confirmações automáticas em operações CRUD
"""

from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import resolve
import json


class AutoConfirmationMiddleware(MiddlewareMixin):
    """
    Middleware que adiciona confirmações automáticas baseadas na URL e método
    """
    
    # URLs que requerem confirmação automática
    CONFIRMATION_PATTERNS = {
        # Beneficiárias
        'members:create': {'entity': 'beneficiária', 'action': 'cadastrar'},
        'members:update': {'entity': 'beneficiária', 'action': 'editar'},
        'members:delete': {'entity': 'beneficiária', 'action': 'excluir'},
        
        # Projetos
        'projects:create': {'entity': 'projeto', 'action': 'cadastrar'},
        'projects:update': {'entity': 'projeto', 'action': 'editar'},
        'projects:delete': {'entity': 'projeto', 'action': 'excluir'},
        
        # Atividades
        'activities:create': {'entity': 'atividade', 'action': 'cadastrar'},
        'activities:update': {'entity': 'atividade', 'action': 'editar'},
        'activities:delete': {'entity': 'atividade', 'action': 'excluir'},
        
        # Workshops
        'workshops:create': {'entity': 'workshop', 'action': 'cadastrar'},
        'workshops:update': {'entity': 'workshop', 'action': 'editar'},
        'workshops:delete': {'entity': 'workshop', 'action': 'excluir'},
    }
    
    def process_request(self, request):
        """Processa requisições para adicionar confirmações"""
        
        # Só processar POST/PUT/PATCH/DELETE
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return None
        
        # Verificar se já foi confirmado
        if request.POST.get('confirmed') == 'true':
            return None
        
        # Resolver URL para obter view name
        try:
            url_match = resolve(request.path_info)
            view_name = url_match.view_name
        except:
            return None
        
        # Verificar se URL requer confirmação
        if view_name not in self.CONFIRMATION_PATTERNS:
            return None
        
        # Obter configuração de confirmação
        config = self.CONFIRMATION_PATTERNS[view_name]
        
        # Se for AJAX, retornar JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'requires_confirmation': True,
                'entity': config['entity'],
                'action': config['action'],
                'message': f"Confirma {config['action']} {config['entity']}?",
                'confirm_url': request.build_absolute_uri(),
            })
        
        # Para requisições normais, renderizar página de confirmação
        context = {
            'entity': config['entity'],
            'action': config['action'],
            'message': f"Confirma {config['action']} {config['entity']}?",
            'confirm_url': request.build_absolute_uri(),
            'cancel_url': request.META.get('HTTP_REFERER', '/'),
            'form_data': request.POST if request.method == 'POST' else None,
        }
        
        return render_to_string('core/confirmation.html', context, request=request)
