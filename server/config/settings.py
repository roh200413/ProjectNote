from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if host]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "server.config.apps.ServerAppConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "server.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [PROJECT_ROOT / "apps" / "web" / "src" / "legacy" / "client"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "server.config.wsgi.application"
ASGI_APPLICATION = "server.config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "projectnote.db",
    }
}

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_ENGINE = "django.contrib.sessions.backends.db"

RESEARCH_NOTES_STORAGE_INTERNAL_ROOT = PROJECT_ROOT / "storage" / "research_notes"
RESEARCH_NOTES_STORAGE_USE_EXTERNAL = (
    os.getenv("RESEARCH_NOTES_STORAGE_USE_EXTERNAL", "false").strip().lower() == "true"
)

if RESEARCH_NOTES_STORAGE_USE_EXTERNAL:
    RESEARCH_NOTES_STORAGE_ROOT = os.getenv(
        "RESEARCH_NOTES_STORAGE_ROOT", str(RESEARCH_NOTES_STORAGE_INTERNAL_ROOT)
    )
else:
    RESEARCH_NOTES_STORAGE_ROOT = str(RESEARCH_NOTES_STORAGE_INTERNAL_ROOT)

Path(RESEARCH_NOTES_STORAGE_ROOT).mkdir(parents=True, exist_ok=True)

X_FRAME_OPTIONS = "SAMEORIGIN"
