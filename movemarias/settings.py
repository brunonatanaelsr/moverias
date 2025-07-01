# Copilot: configurar Django 4.2 LTS.
# - Usar django-environ p/ ler variáveis.
# - Banco default = SQLite (db.sqlite3); se ENV DATABASE_URL presente, usar dj-database-url (Postgres).
# - INSTALLED_APPS: django.contrib.*, rest_framework, allauth, otp, tailwind, members, social, projects, coaching, evolution.
# - Segurança: SECURE_HSTS_SECONDS, SECURE_SSL_REDIRECT (só se not DEBUG), SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE.
# - django-cryptography KEY a partir de ENV.
# - REST_FRAMEWORK auth classes Session + TokenAuth.
# - Static/Media locais; em produção usar S3 via django-storages se ENV=production.

import environ
import os
from pathlib import Path
# Removed custom security imports for easier deployment

# Sentry configuration - import only in production
if os.environ.get('ENVIRONMENT') == 'production':
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment setup with better defaults for easy deployment
env = environ.Env(
    DEBUG=(bool, False),  # Production-safe default
    SECRET_KEY=(str, ''),
    DATABASE_URL=(str, ''),
    ALLOWED_HOSTS=(list, []),
    USE_S3=(bool, False),  # Local storage by default
    ENVIRONMENT=(str, 'development'),
)

# Read .env file if it exists
environ.Env.read_env(BASE_DIR / '.env')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# Simple secret key validation
if not DEBUG and SECRET_KEY == '':
    raise ValueError("SECRET_KEY must be set in production environment")

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
    'localhost', 
    '127.0.0.1', 
    'move.squadsolucoes.com.br', 
    'www.move.squadsolucoes.com.br',
    '145.79.6.36'  # VPS IP
])


# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'crispy_forms',
    'crispy_tailwind',
    'formtools',
    'django_htmx',
    'django_extensions',
    # Celery apps (only when Celery is installed)
    # 'django_celery_beat',
    # 'django_celery_results',
]

LOCAL_APPS = [
    'users',  # Deve ser o primeiro para sobrescrever o modelo de usuário padrão
    'core',
    'dashboard',
    'api',
    'members',
    'social',
    'projects',
    'coaching',
    'evolution',
    'workshops',
    # 'hr',  # Módulo de Recursos Humanos - TEMPORARIAMENTE DESABILITADO
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Custom User Model
AUTH_USER_MODEL = 'users.CustomUser'

ROOT_URLCONF = 'movemarias.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'movemarias.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# SQLite configuration for both development and production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            # Increase timeout for concurrent access
            'timeout': 30,
        }
    }
}

# Optimize SQLite for production use
if not DEBUG:
    # Enable connection pooling for better performance
    DATABASES['default']['CONN_MAX_AGE'] = 60


# Cache Configuration
# https://docs.djangoproject.com/en/5.2/topics/cache/

# Redis cache (preferred for production)
REDIS_URL = env('REDIS_URL', default='')

if REDIS_URL and not DEBUG:
    # Production: Redis cache
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 20,
                    'retry_on_timeout': True,
                },
            },
            'KEY_PREFIX': 'movemarias',
        }
    }
    
    # Use Redis for sessions in production
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
    
elif REDIS_URL:
    # Development with Redis available
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'movemarias_dev',
        }
    }
else:
    # Fallback: Local memory cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'movemarias-cache',
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,
            }
        }
    }

# Cache timeout settings (in seconds)
CACHE_TIMEOUT = {
    'SHORT': 300,     # 5 minutes
    'MEDIUM': 1800,   # 30 minutes
    'LONG': 3600,     # 1 hour
    'VERY_LONG': 86400,  # 24 hours
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

# Password validation - simplified for easier deployment
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Enhanced password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Hasher mais seguro
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Static files management moved to bottom of file

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings (django-allauth v65+)
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# Email Configuration
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Move Marias <noreply@movemarias.org>')
SERVER_EMAIL = env('SERVER_EMAIL', default='Move Marias <server@movemarias.org>')

# Email timeout settings
EMAIL_TIMEOUT = 30

# Security settings - Enhanced for HTTPS
if not DEBUG:
    # HTTPS settings
    SECURE_SSL_REDIRECT = True  # Redirect HTTP to HTTPS
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    X_FRAME_OPTIONS = 'DENY'
    
    # HTTPS session/cookie security
    SESSION_COOKIE_SECURE = True  # Require HTTPS for cookies
    CSRF_COOKIE_SECURE = True     # Require HTTPS for CSRF cookies
    
    # HSTS settings for enhanced security
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    # Development settings
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Configurações de sessão mais seguras
SESSION_COOKIE_AGE = 3600  # 1 hora em produção
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# CSRF melhorado (configurações movidas para baixo)
# CSRF_COOKIE_HTTPONLY = True
# CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'http://127.0.0.1:8000',
    'http://localhost:8000',
])

# Django Cryptography
DJANGO_CRYPTOGRAPHY_KEY = env('DJANGO_CRYPTOGRAPHY_KEY', default='test-key-for-development')

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# Crispy Forms settings
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Static/Media files - using local filesystem storage
USE_S3_RAW = env('USE_S3', default='False')
USE_S3 = str(USE_S3_RAW).strip().lower() in ('1', 'true', 'yes', 'on')

# Force local storage for this deployment
USE_S3 = False

# Always use local filesystem storage
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Static files configuration (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files configuration (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB

# Session and CSRF settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'  # Changed from Strict to Lax for better compatibility
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 hours

# CSRF settings
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'  # Changed from Strict to Lax for better compatibility

# Simple logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
    },
}

# Sentry Configuration for Error Monitoring
if not DEBUG and os.environ.get('SENTRY_DSN'):
    # Import Sentry if available
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        
        sentry_sdk.init(
            dsn=env('SENTRY_DSN'),
            environment=env('SENTRY_ENVIRONMENT', default='production'),
            integrations=[
                DjangoIntegration(
                    transaction_style='url',
                    middleware_spans=True,
                    signals_spans=True,
                    cache_spans=True,
                ),
                RedisIntegration(),
                CeleryIntegration(
                    monitor_beat_tasks=True,
                    propagate_traces=True,
                ),
            ],
            # Performance monitoring
            traces_sample_rate=0.1,  # 10% of transactions
            send_default_pii=False,  # Don't send personal data
            
            # Error filtering
            before_send=lambda event, hint: event if not DEBUG else None,
            
            # Release tracking
            release=env('SENTRY_RELEASE', default=None),
            
            # Additional options
            max_breadcrumbs=50,
            attach_stacktrace=True,
        )
    except ImportError:
        # Sentry not available, continue without it
        pass

# Celery Configuration for Background Tasks
if REDIS_URL:
    CELERY_BROKER_URL = env('CELERY_BROKER_URL', default=f"{REDIS_URL.replace('/0', '/1')}")
    CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default=f"{REDIS_URL.replace('/0', '/2')}")
    
    # Celery settings
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = TIME_ZONE
    CELERY_ENABLE_UTC = True
    
    # Task routing
    CELERY_TASK_ROUTES = {
        'core.tasks.backup_database': {'queue': 'backup'},
        'core.tasks.send_email': {'queue': 'email'},
        'core.tasks.generate_report': {'queue': 'reports'},
    }
    
    # Task time limits
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
    
    # Worker settings
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
    CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
    
    # Beat scheduler
    CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
    
    # Monitoring
    CELERY_SEND_TASK_EVENTS = True
    CELERY_TASK_SEND_SENT_EVENT = True

# Production optimizations
if not DEBUG:
    # Database connection pooling
    DATABASES['default']['CONN_MAX_AGE'] = 60
    
    # Static files compression
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
    
    # Template caching - disable APP_DIRS when using custom loaders
    TEMPLATES[0]['APP_DIRS'] = False
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        ('django.template.loaders.cached.Loader', [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ]),
    ]
