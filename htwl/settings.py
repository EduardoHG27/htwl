import os
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 SEGURIDAD - USAR VARIABLES DE ENTORNO
SECRET_KEY = os.environ.get('SECRET_KEY', 'tu-clave-secreta-local')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# 🌐 ALLOWED_HOSTS - CRÍTICO PARA RAILWAY
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.railway.app',  # Permite todos los subdominios de railway.app
    os.environ.get('RAILWAY_PUBLIC_DOMAIN', ''),  # Dominio dinámico de Railway
    '*',  # Temporal para pruebas (quitar en producción real)
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

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
    'catalogo',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'htwl.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'catalogo.context_processors.carrito_count',  # ← Debe coincidir con el nombre de la función
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

# Archivos multimedia
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'