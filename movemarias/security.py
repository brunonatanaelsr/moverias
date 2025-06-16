# Security configurations for Move Marias
import os
import secrets
from django.core.exceptions import ImproperlyConfigured

def get_env_variable(var_name, default=None):
    """Get environment variable or raise exception"""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        error_msg = f"Set the {var_name} environment variable"
        raise ImproperlyConfigured(error_msg)

def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(50)

def validate_secret_key(secret_key):
    """Validate secret key security"""
    if not secret_key:
        raise ImproperlyConfigured("SECRET_KEY is required")
    
    if len(secret_key) < 50:
        raise ImproperlyConfigured("SECRET_KEY must be at least 50 characters long")
    
    if secret_key.startswith('django-insecure-'):
        raise ImproperlyConfigured("Do not use django-insecure- keys in production")
    
    return True

# Security settings for production
SECURITY_SETTINGS = {
    # HTTPS Settings
    'SECURE_SSL_REDIRECT': True,
    'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https'),
    
    # HSTS Settings
    'SECURE_HSTS_SECONDS': 31536000,  # 1 year
    'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
    'SECURE_HSTS_PRELOAD': True,
    
    # Content Security
    'SECURE_CONTENT_TYPE_NOSNIFF': True,
    'SECURE_BROWSER_XSS_FILTER': True,
    'X_FRAME_OPTIONS': 'DENY',
    
    # Session Security
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Strict',
    'SESSION_COOKIE_AGE': 3600,  # 1 hour
    
    # CSRF Security
    'CSRF_COOKIE_SECURE': True,
    'CSRF_COOKIE_HTTPONLY': True,
    'CSRF_COOKIE_SAMESITE': 'Strict',
    'CSRF_FAILURE_VIEW': 'core.views.csrf_failure',
}

# Content Security Policy
CSP_SETTINGS = {
    'CSP_DEFAULT_SRC': ["'self'"],
    'CSP_SCRIPT_SRC': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
    'CSP_STYLE_SRC': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
    'CSP_IMG_SRC': ["'self'", "data:", "https:"],
    'CSP_FONT_SRC': ["'self'", "https://cdn.jsdelivr.net"],
}

# Rate limiting settings
RATE_LIMIT_SETTINGS = {
    'LOGIN_ATTEMPTS': 5,  # max attempts per IP
    'LOGIN_TIMEOUT': 300,  # 5 minutes
    'API_REQUESTS_PER_MINUTE': 60,
    'CONTACT_FORM_PER_HOUR': 5,
}

# Allowed hosts for production
PRODUCTION_ALLOWED_HOSTS = [
    'movemarias.org',
    'www.movemarias.org',
    # Add your production domains here
]

# Database security
DATABASE_CONN_MAX_AGE = 600
DATABASE_OPTIONS = {
    'connect_timeout': 60,
    'read_timeout': 60,
    'write_timeout': 60,
}
