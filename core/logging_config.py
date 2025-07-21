"""
Configuração de logging estruturado para o sistema MoveMarias
"""
import os
from pathlib import Path

# Base directory for logs
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / 'logs'

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "process": %(process)d, "thread": %(thread)d, "message": "%(message)s"}',
        },
        'security': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "user": "%(user)s", "ip": "%(ip)s", "action": "%(action)s", "resource": "%(resource)s", "result": "%(result)s"}',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file_info': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'movemarias.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'security_log': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'security.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 10,
            'formatter': 'security',
        },
        'performance_log': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'performance.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file_info'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_info', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file_error', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_log', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'security': {
            'handlers': ['security_log'],
            'level': 'INFO',
            'propagate': False,
        },
        'performance': {
            'handlers': ['performance_log'],
            'level': 'INFO',
            'propagate': False,
        },
        'movemarias': {
            'handlers': ['console', 'file_info'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # App-specific loggers
        'users': {
            'handlers': ['file_info', 'security_log'],
            'level': 'INFO',
            'propagate': False,
        },
        'members': {
            'handlers': ['file_info'],
            'level': 'INFO',
            'propagate': False,
        },
        'workshops': {
            'handlers': ['file_info'],
            'level': 'INFO',
            'propagate': False,
        },
        'projects': {
            'handlers': ['file_info'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.upload': {
            'handlers': ['file_info', 'security_log'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


class SecurityLogAdapter:
    """
    Adapter para logs de segurança estruturados
    """
    def __init__(self, logger, extra=None):
        self.logger = logger
        self.extra = extra or {}
    
    def log_auth_attempt(self, user_email, ip_address, success, reason=None):
        """Log de tentativa de autenticação"""
        self.logger.warning(
            "Authentication attempt",
            extra={
                'user': user_email,
                'ip': ip_address,
                'action': 'authentication',
                'resource': 'login',
                'result': 'success' if success else 'failed',
                'reason': reason or ''
            }
        )
    
    def log_permission_denied(self, user, resource, action, ip_address):
        """Log de negação de permissão"""
        self.logger.warning(
            "Permission denied",
            extra={
                'user': user.email if hasattr(user, 'email') else str(user),
                'ip': ip_address,
                'action': action,
                'resource': resource,
                'result': 'denied'
            }
        )
    
    def log_data_access(self, user, resource, action, ip_address, success=True):
        """Log de acesso a dados sensíveis"""
        self.logger.info(
            "Data access",
            extra={
                'user': user.email if hasattr(user, 'email') else str(user),
                'ip': ip_address,
                'action': action,
                'resource': resource,
                'result': 'success' if success else 'failed'
            }
        )


def get_security_logger():
    """
    Factory para obter logger de segurança
    """
    import logging
    logger = logging.getLogger('security')
    return SecurityLogAdapter(logger)


# Performance monitoring helpers
class PerformanceLogger:
    """
    Logger para métricas de performance
    """
    def __init__(self):
        self.logger = logging.getLogger('performance')
    
    def log_query_time(self, query, time_taken, count=None):
        """Log de tempo de query"""
        self.logger.info(
            f"Query performance: {time_taken:.3f}s",
            extra={
                'query_type': 'database',
                'execution_time': time_taken,
                'query_count': count,
                'query': str(query)[:200]  # Truncate long queries
            }
        )
    
    def log_view_response_time(self, view_name, time_taken, status_code):
        """Log de tempo de resposta de view"""
        self.logger.info(
            f"View performance: {view_name} - {time_taken:.3f}s",
            extra={
                'view_name': view_name,
                'response_time': time_taken,
                'status_code': status_code,
                'type': 'view_performance'
            }
        )


def get_performance_logger():
    """
    Factory para obter logger de performance
    """
    return PerformanceLogger()
