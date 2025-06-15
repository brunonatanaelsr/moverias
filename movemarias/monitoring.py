# Enhanced logging configuration for Move Marias
import os
import logging.config
from pathlib import Path

# Base directory for logs
LOG_DIR = Path('/var/log/movemarias')
LOG_DIR.mkdir(exist_ok=True)

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
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
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'debug.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_info': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'django.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'error.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'security.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 20,
            'formatter': 'json',
        },
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'performance.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'database_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'database.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_info', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file_error', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['database_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'movemarias': {
            'handlers': ['console', 'file_info', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'movemarias.performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'movemarias.security': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'root': {
            'handlers': ['console', 'file_error'],
            'level': 'WARNING',
        },
    },
}

def setup_logging():
    """Configure logging for the application"""
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Test logging
    logger = logging.getLogger('movemarias')
    logger.info('Logging configuration loaded successfully')

# Performance monitoring
class PerformanceLogger:
    def __init__(self):
        self.logger = logging.getLogger('movemarias.performance')
    
    def log_slow_query(self, query, duration):
        self.logger.warning(f"Slow query detected: {duration:.2f}s - {query}")
    
    def log_view_performance(self, view_name, duration, method='GET'):
        if duration > 1.0:  # Log views taking more than 1 second
            self.logger.info(f"Slow view: {view_name} ({method}) took {duration:.2f}s")
    
    def log_cache_hit(self, cache_key, hit=True):
        status = "HIT" if hit else "MISS"
        self.logger.debug(f"Cache {status}: {cache_key}")

# Security monitoring
class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger('movemarias.security')
    
    def log_login_attempt(self, username, success=True, ip_address=None):
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Login {status}: {username} from {ip_address}")
    
    def log_permission_denied(self, user, resource, ip_address=None):
        self.logger.warning(f"Permission denied: {user} tried to access {resource} from {ip_address}")
    
    def log_suspicious_activity(self, description, ip_address=None, user=None):
        self.logger.warning(f"Suspicious activity: {description} from {ip_address} (user: {user})")

# Initialize loggers
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()
