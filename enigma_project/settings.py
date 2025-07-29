import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    print("ATTENZIONE: SECRET_KEY non impostata nell'ambiente!")
    if os.environ.get('DEBUG', 'False') == 'True':
        SECRET_KEY = 'django-insecure-chiave-provvisoria-per-sviluppo-locale'

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = ALLOWED_HOSTS_ENV.split(',') if ALLOWED_HOSTS_ENV else []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
if '127.0.0.1' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('127.0.0.1')
if 'localhost' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('localhost')
if not ALLOWED_HOSTS and DEBUG:
     ALLOWED_HOSTS = ['localhost', '127.0.0.1']
elif not ALLOWED_HOSTS and not DEBUG:
     print("ATTENZIONE: ALLOWED_HOSTS è vuota in modalità non-DEBUG!")

INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'enigmas', 'django.contrib.sites', 'allauth', 'allauth.account',
]
SITE_ID = 1
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
ROOT_URLCONF = 'enigma_project.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug', 'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages',
                'enigmas.context_processors.unread_notifications_context',
            ],
        },
    },
]
WSGI_APPLICATION = 'enigma_project.wsgi.application'
DATABASE_URL_ENV = os.environ.get('DATABASE_URL')
if DATABASE_URL_ENV:
    print("INFO: Trovata variabile DATABASE_URL, si configura per DB esterno.")
    DATABASES = {'default': dj_database_url.config(default=DATABASE_URL_ENV, conn_max_age=600, ssl_require=True)}
else:
    print("INFO: Variabile DATABASE_URL non trovata, si configura per SQLite locale.")
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'it-IT'
TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = 'account_login'
LOGOUT_REDIRECT_URL = '/'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True') == 'True'
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'True') == 'True'
CSRF_TRUSTED_ORIGINS_ENV = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS_ENV.split(',') if CSRF_TRUSTED_ORIGINS_ENV else []
if RENDER_EXTERNAL_HOSTNAME and f'https://{RENDER_EXTERNAL_HOSTNAME}' not in CSRF_TRUSTED_ORIGINS:
     CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

# Impostazioni Email
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("INFO: Usando Console Email Backend (DEBUG=True)")
else:
    # --- MODIFICA DI SICUREZZA PER IL DEBUG IN PRODUZIONE ---
    # Invece di usare SMTP, che può fallire se le variabili non sono impostate,
    # usiamo il backend 'console' che stampa le email nei log di Render.
    # Questo previene il crash del server (errore 500) durante il login.
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("ATTENZIONE: L'email backend di produzione è impostato su 'console' per il debug.")
    # Una volta che le variabili d'ambiente per SendGrid saranno corrette su Render,
    # potrai ripristinare la configurazione SMTP originale.

# --- MODIFICHE PER SISTEMA DI APPROVAZIONE ---
# 1. Disattiva la verifica via email obbligatoria
ACCOUNT_EMAIL_VERIFICATION = 'none'

# 2. Dice a allauth di usare il nostro "adattatore" custom per la registrazione
ACCOUNT_ADAPTER = 'enigmas.adapters.AccountAdapter'

# Impostazioni specifiche django-allauth (le altre rimangono)
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[Illusion Game] '
