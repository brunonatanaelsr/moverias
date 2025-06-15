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
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment setup
env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, 'django-insecure-dev-key'),
    DATABASE_URL=(str, ''),
)

# Read .env file if it exists
environ.Env.read_env(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])


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

# Default: SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# If DATABASE_URL is set, use it (for production with Postgres)
if env('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.parse(env('DATABASE_URL'))


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

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
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

# Security settings
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000  # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    X_FRAME_OPTIONS = 'DENY'
else:
    # Configurações de desenvolvimento mais seguras
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Configurações de sessão mais seguras
SESSION_COOKIE_AGE = 3600  # 1 hora em produção
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# CSRF melhorado
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

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
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
