"""Django settings for the movies administration project.

No credential is ever written by hand in this file. The secret key and the
optional superuser password are read from the process environment, falling
back to a local ``.env`` file that is generated on the first run and kept out
of version control.
"""

import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = BASE_DIR / '.env'


def _parse_env_file(path):
    """Return the key/value pairs stored in a simple ``.env`` file."""
    values = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _load_file_env():
    """Create ``.env`` on first run and return its values."""
    values = _parse_env_file(ENV_FILE)
    if 'DJANGO_SECRET_KEY' not in values:
        if not ENV_FILE.exists():
            ENV_FILE.write_text(
                '# Generated automatically on first run. Do not commit.\n'
                f'DJANGO_SECRET_KEY={secrets.token_urlsafe(64)}\n',
                encoding='utf-8',
            )
        values = _parse_env_file(ENV_FILE)
    return values


FILE_ENV = _load_file_env()


def get_setting(name, default=None):
    """Read a setting from the environment, then from ``.env``."""
    return os.environ.get(name) or FILE_ENV.get(name) or default


SECRET_KEY = get_setting('DJANGO_SECRET_KEY')

DEBUG = get_setting('DJANGO_DEBUG', '1') == '1'

ALLOWED_HOSTS = [
    host.strip()
    for host in get_setting('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in get_setting('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'movies',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': get_setting('DJANGO_DB_NAME', str(BASE_DIR / 'db.sqlite3')),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Lima'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# The rating scale used by the movies application.
RATING_MIN_SCORE = 1
RATING_MAX_SCORE = 10
