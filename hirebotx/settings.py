from pathlib import Path
import os
from dotenv import load_dotenv
from django.urls import reverse_lazy
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ========================
# ENV + CORE SETTINGS
# ========================
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")

DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    'hirebotx.onrender.com',
    '127.0.0.1',
    'localhost',
    'https://hirebotx.onrender.com',
]

# ========================
# APPLICATIONS
# ========================
INSTALLED_APPS = [

    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "django.contrib.sites",
    'django.contrib.humanize',

    'user',
    'jobs',
    'applications',
    'ats_checker',
    'company.apps.CompanyConfig',
]


# ========================
# MIDDLEWARE
# ========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
]

# Add Whitenoise ONLY in production
if not DEBUG:
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')

MIDDLEWARE += [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'user.middleware.UpdateLastActivityMiddleware',
]


ROOT_URLCONF = 'hirebotx.urls'


# ========================
# TEMPLATES
# ========================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "user.context_processors.global_context",
            ],
        },
    },
]


WSGI_APPLICATION = 'hirebotx.wsgi.application'


# ========================
# DATABASE
# ========================
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': dj_database_url.config(
            default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
        )
    }


# ========================
# STATIC FILES
# ========================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Production static handling
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'


# ========================
# MEDIA FILES
# ========================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ========================
# AUTH
# ========================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = reverse_lazy('custom_redirect')
LOGOUT_REDIRECT_URL = '/'


# ========================
# INTERNATIONALIZATION
# ========================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# ========================
# DEFAULT PK
# ========================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ========================
# EMAIL - SEND REAL EMAILS IN BOTH DEVELOPMENT AND PRODUCTION
# ========================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Add timeout to prevent hanging (5 seconds)
EMAIL_TIMEOUT = 5

# Check if email credentials are provided
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    print("=" * 50)
    print("WARNING: Email credentials not found in .env file!")
    print("Please add EMAIL_HOST_USER and EMAIL_HOST_PASSWORD to your .env file")
    print("Using console backend for now...")
    print("=" * 50)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# ========================
# CUSTOM
# ========================
SITE_ID = 1
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000")
DOMAIN = os.getenv("DOMAIN", "http://127.0.0.1:8000")

JAZZMIN_SETTINGS = {
    "copyright": "HireBotx",
}


# ========================
# LOGGING CONFIGURATION
# ========================
# Create logs directory only in production
if not DEBUG:
    logs_dir = BASE_DIR / 'logs'
    if not logs_dir.exists():
        logs_dir.mkdir(exist_ok=True)

# Configure logging based on environment
if DEBUG:
    # Development: Only console logging
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '{levelname} {asctime} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            'user': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
else:
    # Production: Console + File logging
    LOGGING = {
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
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': BASE_DIR / 'logs' / 'email.log',
                'formatter': 'verbose',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            'user': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }


# ========================
# SECURITY (ONLY PROD)
# ========================
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True