"""
Base settings shared across all environments.
"""

import os
from pathlib import Path

from django.templatetags.static import static
from django.urls import reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "insecure-dev-key-change-in-production")

INSTALLED_APPS = [
    # Unfold must come before django.contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Project apps
    "apps.accounts",
    "apps.parish",
    "apps.gallery",
    "apps.contact",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization - Brazilian Portuguese
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (uploads)
MEDIA_URL = "media/"
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", BASE_DIR / "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login
LOGIN_URL = reverse_lazy("admin:login")
LOGIN_REDIRECT_URL = reverse_lazy("admin:index")

# Image processing sizes
IMAGE_SIZES = {
    "thumb": {"max_width": 300, "max_height": 300, "quality": 80},
    "medium": {"max_width": 800, "max_height": 800, "quality": 85},
    "large": {"max_width": 1200, "max_height": 1200, "quality": 90},
}

# Unfold admin config
UNFOLD = {
    "SITE_TITLE": "Igreja São Sebastião",
    "SITE_HEADER": "Igreja São Sebastião",
    "SITE_SYMBOL": "church",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "STYLES": [
        lambda request: static("css/admin_custom.css"),
    ],
    "COLORS": {
        "primary": {
            "50": "oklch(97% .02 285)",
            "100": "oklch(93% .04 285)",
            "200": "oklch(87% .08 285)",
            "300": "oklch(78% .13 285)",
            "400": "oklch(68% .19 280)",
            "500": "oklch(58% .22 278)",
            "600": "oklch(52% .24 278)",
            "700": "oklch(45% .22 280)",
            "800": "oklch(38% .18 282)",
            "900": "oklch(32% .15 284)",
            "950": "oklch(24% .12 285)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Dashboard",
                "items": [
                    {
                        "title": "Painel",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:dashboard"),
                    },
                ],
            },
            {
                "title": "Conteúdo",
                "collapsible": True,
                "items": [
                    {
                        "title": "Notícias",
                        "icon": "newspaper",
                        "link": reverse_lazy("admin:parish_news_changelist"),
                    },
                    {
                        "title": "Galeria",
                        "icon": "photo_library",
                        "link": reverse_lazy("admin:gallery_galleryimage_changelist"),
                    },
                ],
            },
            {
                "title": "Configurações",
                "collapsible": True,
                "items": [
                    {
                        "title": "Conteúdo do Site",
                        "icon": "edit_note",
                        "link": reverse_lazy("admin:site-content"),
                    },
                    {
                        "title": "Imagens do Site",
                        "icon": "image",
                        "link": reverse_lazy("admin:site-images"),
                    },
                    {
                        "title": "Horários",
                        "icon": "schedule",
                        "link": reverse_lazy("admin:parish_massschedule_changelist"),
                    },
                    {
                        "title": "Contatos",
                        "icon": "contacts",
                        "link": reverse_lazy("admin:parish_contactinfo_changelist"),
                    },
                    {
                        "title": "Configurações Gerais",
                        "icon": "settings",
                        "link": reverse_lazy("admin:parish_siteconfiguration_changelist"),
                    },
                ],
            },
            {
                "title": "Comunicação",
                "collapsible": True,
                "items": [
                    {
                        "title": "Mensagens",
                        "icon": "mail",
                        "link": reverse_lazy("admin:contact_contactmessage_changelist"),
                    },
                    {
                        "title": "Banco de Imagens",
                        "icon": "collections",
                        "link": reverse_lazy("admin:image-bank"),
                    },
                ],
            },
            {
                "title": "Sistema",
                "collapsible": True,
                "items": [
                    {
                        "title": "Usuários",
                        "icon": "people",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                    {
                        "title": "Logs de Auditoria",
                        "icon": "history",
                        "link": reverse_lazy("admin:accounts_auditlog_changelist"),
                    },
                    {
                        "title": "Ver Site",
                        "icon": "open_in_new",
                        "link": "/",
                    },
                ],
            },
        ],
    },
}
