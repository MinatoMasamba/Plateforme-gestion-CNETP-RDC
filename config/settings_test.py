"""Settings overrides for the automated test suite.

Importing everything from the base settings keeps the test environment
identical to production for models, apps and middleware, while neutralising
the parts that must never run during tests:

* real outbound email (Gmail SMTP in ``.env``) -> locmem backend
* slow password hashing (PBKDF2) -> MD5 hasher
* external LLM / notification / Celery brokers -> eager / in-memory
"""
from .settings import *  # noqa: F401,F403


# --- Email: never hit the network during tests -----------------------------
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
DEFAULT_FROM_EMAIL = 'tests@cnetp.cd'

# --- Speed up authentication ------------------------------------------------
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# --- Background tasks run inline -------------------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_BROKER_URL = ''
CELERY_RESULT_BACKEND = ''

# --- Channels / cache without Redis ----------------------------------------
REDIS_AVAILABLE = False
CHANNEL_LAYERS = {
    'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'cnetp-test-cache',
    }
}

# --- Disable outbound notification providers --------------------------------
NOTIFICATION_SETTINGS = {
    'EMAIL_ENABLED': True,
    'FCM_ENABLED': False,
    'RETRY_ATTEMPTS': 1,
    'RETRY_DELAY_SEC': 0,
}
TWILIO_ACCOUNT_SID = ''
TWILIO_AUTH_TOKEN = ''
TWILIO_WHATSAPP_FROM = ''
FIREBASE_CREDENTIALS_PATH = ''
FIREBASE_CREDENTIALS_JSON = ''

# --- Disable external LLM calls --------------------------------------------
DEEPSEEK_API_KEY = ''

# --- Static files -----------------------------------------------------------
DEBUG = False

# WhiteNoise is unnecessary during tests and warns when STATIC_ROOT is absent.
MIDDLEWARE = [m for m in MIDDLEWARE if 'whitenoise' not in m]

# Keep plain storage in tests (no collectstatic / manifest required).
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}
