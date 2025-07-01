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

# Security settings for production (relaxed for easier deployment)
SECURITY_SETTINGS = {
    # HTTPS Settings - relaxed for initial deployment
    'SECURE_SSL_REDIRECT': False,  # Disabled for HTTP testing
    'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https'),
    
    # HSTS Settings - disabled for initial deployment
    'SECURE_HSTS_SECONDS': 0,  # Disabled
    'SECURE_HSTS_INCLUDE_SUBDOMAINS': False,
    'SECURE_HSTS_PRELOAD': False,
    
    # Content Security
    'SECURE_CONTENT_TYPE_NOSNIFF': True,
    'SECURE_BROWSER_XSS_FILTER': True,
    'X_FRAME_OPTIONS': 'SAMEORIGIN',  # Relaxed from DENY
    
    # Session Security - relaxed
    'SESSION_COOKIE_SECURE': False,  # Allow HTTP cookies
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',  # Relaxed from Strict
    'SESSION_COOKIE_AGE': 86400,  # 24 hours (increased)
    
    # CSRF Security - relaxed
    'CSRF_COOKIE_SECURE': False,  # Allow HTTP cookies
    'CSRF_COOKIE_HTTPONLY': False,  # Allow JS access if needed
    'CSRF_COOKIE_SAMESITE': 'Lax',  # Relaxed from Strict
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
