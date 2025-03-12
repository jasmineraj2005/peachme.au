from pathlib import Path
import os

# 📌 Define BASE_DIR first
BASE_DIR = Path(__file__).resolve().parent.parent

# 📌 SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-9m1@%f-!epw9v(e4$p!6$3%9=us2p@6fsttw+l=d=&&b=p@&f2'

# 📌 SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # ✅ Move this here (before using it)

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


# ✅ Allow requests from Next.js frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Allow local Next.js
    "http://192.168.20.24:3000",  # ✅ Allow your local network IP
]

# ✅ Allow all HTTP methods
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "OPTIONS",
]

# ✅ Allow sending cookies, authentication
CORS_ALLOW_CREDENTIALS = True

# ✅ If you want to allow ANY frontend (not recommended for production)
CORS_ALLOW_ALL_ORIGINS = True  # ⚠️ Temporary fix, remove in production


# ✅ Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'api',
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # ✅ Ensure this is at the TOP
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# ✅ Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ✅ Password Validation
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

# ✅ Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ✅ Static & Media File Settings
STATIC_URL = 'static/'

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ✅ Primary Key Type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
