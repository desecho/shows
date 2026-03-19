"""Django settings."""

from datetime import timedelta
from os import getenv
from os.path import abspath, dirname, join
from urllib.parse import urljoin

import django_stubs_ext
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from showsapp.types import TemplatesSettings, TrailerSitesSettings

django_stubs_ext.monkeypatch()

SENTRY_TRACE_SAMPLING = 0.5

sentry_sdk.init(
    dsn=getenv("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=SENTRY_TRACE_SAMPLING,
    send_default_pii=True,
)

# Custom
IS_DEV = bool(getenv("IS_DEV"))
IS_CELERY_DEBUG = bool(getenv("IS_CELERY_DEBUG"))
COLLECT_STATIC = bool(getenv("COLLECT_STATIC"))
SRC_DIR = dirname(dirname(abspath(__file__)))
PROJECT = "shows"
APP = "showsapp"
PROJECT_DIR = dirname(SRC_DIR)
PROJECT_DOMAIN = getenv("PROJECT_DOMAIN")
REDIS_URL = getenv("REDIS_URL")
LANGUAGE_EN = "en"
LANGUAGE_RU = "ru"

# Debug
DEBUG = bool(getenv("DEBUG"))
INTERNAL_IPS = [getenv("INTERNAL_IP")]

ADMIN_EMAIL = getenv("ADMIN_EMAIL")
SECRET_KEY = getenv("SECRET_KEY", "key")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": PROJECT,
        "USER": getenv("DB_USER"),
        "PASSWORD": getenv("DB_PASSWORD"),
        "HOST": getenv("DB_HOST"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}
ROOT_URLCONF = f"{PROJECT}.urls"
WSGI_APPLICATION = f"{PROJECT}.wsgi.application"
SESSION_SAVE_EVERY_REQUEST = True

# Email
EMAIL_USE_SSL = bool(getenv("EMAIL_USE_SSL", "True"))
EMAIL_HOST = getenv("EMAIL_HOST")
EMAIL_HOST_USER = getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = getenv("EMAIL_HOST_PASSWORD")
EMAIL_PORT = int(getenv("EMAIL_PORT", "465"))
DEFAULT_FROM_EMAIL = ADMIN_EMAIL

# Allowed hosts
ALLOWED_HOSTS = [PROJECT_DOMAIN, "127.0.0.1"]

# Internationalization
LANGUAGE_CODE = LANGUAGE_EN
LANGUAGES = (
    (LANGUAGE_EN, "English"),
    (LANGUAGE_RU, "Русский"),
)
LOCALE_PATHS = (join(SRC_DIR, "locale"),)

# Timezone
TIME_ZONE = "US/Eastern"
USE_TZ = True

TEMPLATES: list[TemplatesSettings] = [
    {
        "NAME": "Main",
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [join(SRC_DIR, "templates")],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ],
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                )
            ],
            "builtins": ["django.templatetags.static"],
        },
    },
]
if IS_DEV:  # pragma: no cover
    TEMPLATES[0]["OPTIONS"]["loaders"] = [
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom
    "django.middleware.gzip.GZipMiddleware",
    "custom_anonymous.middleware.AuthenticationMiddleware",
    "admin_reorder.middleware.ModelAdminReorder",
    "showsapp.middleware.TimezoneMiddleware",
]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Custom
    "admin_reorder",
    "django_countries",
    "django_celery_results",
    "rest_framework",
    "corsheaders",
    "rest_registration",
    APP,
]
if DEBUG:  # pragma: no cover
    INSTALLED_APPS += []

if IS_DEV or COLLECT_STATIC:  # pragma: no cover
    INSTALLED_APPS.append("django.contrib.staticfiles")

# Security
DISABLE_CSRF = bool(getenv("DISABLE_CSRF"))
if not DISABLE_CSRF:  # pragma: no cover
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = [f"https://{PROJECT_DOMAIN}"]

# Authentication
AUTH_USER_MODEL = "showsapp.User"
AUTH_ANONYMOUS_MODEL = "showsapp.models.UserAnonymous"
AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# Login
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/login/"
LOGIN_ERROR_URL = "/login-error/"

# Static files
STATICFILES_DIR = join(SRC_DIR, APP, "static")
if IS_DEV:  # pragma: no cover
    STATICFILES_DIRS = (STATICFILES_DIR,)
    STATIC_ROOT = None
else:
    STATIC_ROOT = join(PROJECT_DIR, "static")

STATIC_URL = getenv("STATIC_URL", "/static/")

# Media files
MEDIA_ROOT = join(PROJECT_DIR, "media")
MEDIA_URL = "/media/"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# --== Modules settings ==--

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": [
        "showsapp.renderers.CountryJSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=365),
}

FRONTEND_URL = getenv("FRONTEND_URL")
CORS_ALLOWED_ORIGINS = [FRONTEND_URL]
FRONTEND_URL2 = getenv("FRONTEND_URL2")
if FRONTEND_URL2:  # pragma: no cover
    CORS_ALLOWED_ORIGINS.append(FRONTEND_URL2)

REST_REGISTRATION = {
    "VERIFICATION_FROM_EMAIL": ADMIN_EMAIL,
    "REGISTER_EMAIL_VERIFICATION_ENABLED": False,
    "RESET_PASSWORD_VERIFICATION_URL": f"{FRONTEND_URL}/reset-password/",
    "REGISTER_VERIFICATION_URL": f"{FRONTEND_URL}/verify-user/",
    "REGISTER_SERIALIZER_PASSWORD_CONFIRM": False,
    "CHANGE_PASSWORD_SERIALIZER_PASSWORD_CONFIRM": False,
}

# django-modeladmin-reorder
ADMIN_REORDER = [
    {
        "app": APP,
        "models": (
            "showsapp.User",
            "showsapp.Show",
            "showsapp.Record",
            "showsapp.List",
            "showsapp.Provider",
            "showsapp.ProviderRecord",
        ),
    },
]

if IS_CELERY_DEBUG:  # pragma: no cover
    ADMIN_REORDER.append(
        {
            "app": "django_celery_results",
            "models": ("django_celery_results.TaskResult",),
        }
    )

# django-modeltranslation
MODELTRANSLATION_CUSTOM_FIELDS = ("JSONField",)

# Celery
CELERY_CACHE_BACKEND = "default"
if IS_CELERY_DEBUG:  # pragma: no cover
    CELERY_RESULT_BACKEND = "django-db"
else:
    CELERY_RESULT_BACKEND = f"{REDIS_URL}0"
CELERY_BROKER_URL = REDIS_URL
CELERY_TIMEZONE = TIME_ZONE

# --== Project settings ==--

REQUESTS_TIMEOUT = 5

# Search settings
MAX_RESULTS = 50
MIN_POPULARITY = 1.5

# Posters
NO_POSTER_SMALL_IMAGE_URL = "img/no_poster_small.png"
NO_POSTER_NORMAL_IMAGE_URL = "img/no_poster_normal.png"
NO_POSTER_BIG_IMAGE_URL = "img/no_poster_big.png"
POSTER_SIZE_SMALL = "w92"
POSTER_SIZE_NORMAL = "w185"
POSTER_SIZE_BIG = "w500"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/"

PROVIDERS_IMG_DIR = join(PROJECT_DIR, "frontend", "public", "img", "providers")
TMDB_BASE_URL = "https://www.themoviedb.org/"
TMDB_SHOW_BASE_URL = urljoin(TMDB_BASE_URL, "tv/")
TMDB_PROVIDER_BASE_URL = urljoin(TMDB_BASE_URL, "t/p/original/")
TMDB_API_BASE_URL = "https://api.themoviedb.org/3/"
IMDB_BASE_URL = "http://www.imdb.com/title/"
RECORDS_ON_PAGE = 50
PEOPLE_ON_PAGE = 25
OMDB_BASE_URL = "http://www.omdbapi.com/"
TRAILER_SITES: TrailerSitesSettings = {
    "YouTube": "https://www.youtube.com/watch?v=",
    "Vimeo": "https://vimeo.com/",
}
IS_TEST = False
INCLUDE_ADULT = False

# Watch data
PROVIDERS_SUPPORTED_COUNTRIES = ("RU", "CA", "US")
# Number of min days that need to pass before the next watch data update
WATCH_DATA_UPDATE_MIN_DAYS = 3

# API Keys
TMDB_KEY = getenv("TMDB_KEY")
OMDB_KEY = getenv("OMDB_KEY")
OPENAI_API_KEY = getenv("OPENAI_API_KEY")

# AI Recommendations
AI_MAX_RECOMMENDATIONS = 50
AI_MIN_RECOMMENDATIONS = 1
AI_MIN_RATING = 0
AI_MAX_RATING = 5
AI_MAX_SHOW_TITLE_LENGTH = 100

OPENAI_MODEL = "gpt-5-mini"
OPENAI_MAX_TOKENS = 10000

# TV Show Genres
MAIN_GENRES = [
    "Action & Adventure",
    "Animation",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Family",
    "Kids",
    "Mystery",
    "News",
    "Reality",
    "Sci-Fi & Fantasy",
    "Soap",
    "Talk",
    "War & Politics",
    "Western",
]

SUBGENRES = [
    "Thriller",
    "Horror",
    "Romance",
    "Medical Drama",
    "Legal Drama",
    "Procedural",
    "Sitcom",
    "Anthology",
    "Miniseries",
    "Docuseries",
    "True Crime",
    "Superhero",
    "Anime",
    "Period Drama",
    "Mockumentary",
]

# Storage configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "showsapp.openai.client": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}
