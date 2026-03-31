import os
import dj_database_url
from pathlib import Path
import logging
import json
import cloudinary
import cloudinary.uploader
import cloudinary.api

BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 SEGURIDAD - USAR VARIABLES DE ENTORNO
SECRET_KEY = os.environ.get('SECRET_KEY', 'tu-clave-secreta-local')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# 🌐 ALLOWED_HOSTS - CRÍTICO PARA RAILWAY
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.railway.app',  # Permite todos los subdominios de railway.app
    os.environ.get('RAILWAY_PUBLIC_DOMAIN', ''),  # Dominio dinámico de Railway
]

# 🔐 CSRF TRUSTED ORIGINS - NECESARIO PARA ADMIN EN PRODUCCIÓN
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',  # Permite todos los subdominios HTTPS de Railway
    'http://localhost:8000',  # Para desarrollo local
    'http://127.0.0.1:8000',
]

# Agregar dominio dinámico de Railway si existe
if os.environ.get('RAILWAY_PUBLIC_DOMAIN'):
    domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    if f'https://{domain}' not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(f'https://{domain}')
    if f'http://{domain}' not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(f'http://{domain}')

IS_PRODUCTION = 'DATABASE_URL' in os.environ

if IS_PRODUCTION:
    # Configuración para producción (Railway)
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    # Configuración para desarrollo local
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = None
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
    'django.contrib.sites',
    'catalogo',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# Configuración de allauth
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Cambiado a mandatory
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False  # Opcional: permitir login con email
ACCOUNT_AUTHENTICATION_METHOD = 'email'  # Usar email como método principal
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_METHODS = {'email'}  # Solo email para login
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*'] 

SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'  # Forzar verificación de email
SOCIALACCOUNT_EMAIL_REQUIRED = False

# Para verificación de correo
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = '/'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3

SOCIALACCOUNT_AUTO_SIGNUP = True  # No auto-crear cuenta sin verificar
SOCIALACCOUNT_LOGIN_ON_GET = True 
SOCIALACCOUNT_ADAPTER = 'catalogo.adapters.CustomSocialAccountAdapter'


SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
            'prompt': 'select_account',  # Forzar selección de cuenta
        },
        'OAUTH_PKCE_ENABLED': True,
        'VERIFIED_EMAIL': True,  # Google ya verifica emails, pero forzamos validación
    }
}

# URLs de redirección
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# Si estás en desarrollo, agrega esto para HTTP
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'

# Agregar las credenciales de Google (al final del archivo)
# ¡IMPORTANTE! Usa las que copiaste de Google Cloud Console
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('GOOGLE_OAUTH2_SECRET', '') # Reemplaza con tu Client Secret

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  
]

ROOT_URLCONF = 'htwl.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Directorio global de templates (si existe)
        'APP_DIRS': True,  # Esto es CLAVE - busca plantillas en templates/ de cada app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'catalogo.context_processors.carrito_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'htwl.wsgi.application'

# BASE DE DATOS - PostgreSQL en producción, SQLite en local
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Validación de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# DATOS BANCARIOS PARA TRANSFERENCIAS - Usando JSON desde variable de entorno
DATOS_BANCARIOS_JSON = os.environ.get('DATOS_BANCARIOS_JSON', '')

if DATOS_BANCARIOS_JSON:
    try:
        DATOS_BANCARIOS = json.loads(DATOS_BANCARIOS_JSON)
        # Validar que tenga los campos mínimos requeridos
        required_fields = ['banco', 'titular', 'cuenta', 'clabe', 'instrucciones']
        missing_fields = [field for field in required_fields if not DATOS_BANCARIOS.get(field)]
        if missing_fields and IS_PRODUCTION:
            import warnings
            warnings.warn(f"DATOS_BANCARIOS faltan campos: {missing_fields}")
    except json.JSONDecodeError as e:
        # Si hay error en el JSON, usar valores por defecto
        DATOS_BANCARIOS = {
            'banco': 'Error en configuración',
            'titular': 'Contactar al administrador',
            'cuenta': 'No disponible',
            'clabe': 'No disponible',
            'tarjeta': '',
            'instrucciones': 'Error en configuración de pago. Por favor contacta al administrador.',
            'email_contacto': 'admin@tutienda.com',
            'telefono_contacto': '55 1234 5678',
        }
        if IS_PRODUCTION:
            # En producción, loguear el error
            import logging
            logging.error(f"Error parsing DATOS_BANCARIOS_JSON: {e}")
else:
    # Configuración por defecto para desarrollo local
    DATOS_BANCARIOS = {
        'banco': 'BBVA México',
        'titular': 'Hot Wheels Store S.A. de C.V.',
        'cuenta': '1234 5678 9012 3456',
        'clabe': '012345678901234567',
        'tarjeta': '1234 5678 9012 3456',
        'instrucciones': 'Realiza la transferencia y sube el comprobante en formato PDF o imagen',
        'email_contacto': 'ventas@hotwheelstore.com',
        'telefono_contacto': '55 1234 5678',
    }

# Idioma y zona horaria
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 5. LOGS Y MONITOREO
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'csrf_debug.log',
        },
    },
    'loggers': {
        'django.security.csrf': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',  # Cambiar a DEBUG temporalmente
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

if not DEBUG:
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
        'SECURE': True,
    }
    
    # Usar Cloudinary para archivos media
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    
    # URL de Cloudinary para archivos media
    MEDIA_URL = f'https://res.cloudinary.com/{os.environ.get("CLOUDINARY_CLOUD_NAME")}/image/upload/'
    
    # MEDIA_ROOT NO se usa con Cloudinary, pero lo dejamos por compatibilidad
    MEDIA_ROOT = BASE_DIR / 'media'  # Esto no se usará realmente
else:
    # Desarrollo local
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# 6. SEGURIDAD ADICIONAL
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:  # Solo en producción
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_HSTS_SECONDS = 0

##SECURE_SSL_REDIRECT = True
##SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
##ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
