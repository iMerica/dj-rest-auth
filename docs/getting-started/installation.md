# Installation

This guide covers all installation scenarios for dj-rest-auth.

## Basic Installation

### 1. Install the package

```bash
pip install dj-rest-auth
```

### 2. Add to installed apps

```python title="settings.py"
INSTALLED_APPS = [
    # Django apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    # ...
    
    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    
    # dj-rest-auth
    'dj_rest_auth',
]
```

!!! note "Dependencies"
    dj-rest-auth requires Django REST Framework. Make sure both `rest_framework` and `rest_framework.authtoken` are in your `INSTALLED_APPS`.

### 3. Add URL patterns

```python title="urls.py"
from django.urls import path, include

urlpatterns = [
    # ...
    path('api/auth/', include('dj_rest_auth.urls')),
]
```

### 4. Run migrations

```bash
python manage.py migrate
```

You now have these endpoints available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login/` | POST | Obtain auth token |
| `/api/auth/logout/` | POST | Revoke auth token |
| `/api/auth/password/reset/` | POST | Request password reset email |
| `/api/auth/password/reset/confirm/` | POST | Confirm password reset |
| `/api/auth/password/change/` | POST | Change password |
| `/api/auth/user/` | GET, PUT, PATCH | User details |

---

## Registration (Optional)

To enable user registration with email verification, you need django-allauth.

### 1. Install with social extras

```bash
pip install 'dj-rest-auth[with-social]'
```

This installs django-allauth as a dependency.

### 2. Configure installed apps

```python title="settings.py"
INSTALLED_APPS = [
    # Django apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',  # Required by allauth
    # ...
    
    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',  # Only if using social auth
    
    # dj-rest-auth
    'dj_rest_auth',
    'dj_rest_auth.registration',
]

# Required by django-allauth
SITE_ID = 1
```

### 3. Add allauth middleware

```python title="settings.py"
MIDDLEWARE = [
    # ...
    'allauth.account.middleware.AccountMiddleware',
]
```

!!! warning "Required Middleware"
    The `AccountMiddleware` is required by django-allauth >= 0.56.0. Without it, you'll get an `ImproperlyConfigured` error.

### 4. Add registration URLs

```python title="urls.py"
from django.urls import path, include

urlpatterns = [
    # ...
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
]
```

### 5. Run migrations

```bash
python manage.py migrate
```

You now have additional endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/registration/` | POST | Register new user |
| `/api/auth/registration/verify-email/` | POST | Verify email address |
| `/api/auth/registration/resend-email/` | POST | Resend verification email |

---

## JWT Authentication (Optional)

By default, dj-rest-auth uses Django REST Framework's token authentication. For JWT support with HTTP-only cookies (recommended for SPAs), follow these steps.

### 1. Install SimpleJWT

```bash
pip install djangorestframework-simplejwt
```

### 2. Configure authentication classes

```python title="settings.py"
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
    ],
}
```

### 3. Enable JWT in dj-rest-auth

```python title="settings.py"
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'access-token',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh-token',
    'JWT_AUTH_HTTPONLY': True,
    'JWT_AUTH_SECURE': True,  # Set to True in production (HTTPS)
    'JWT_AUTH_SAMESITE': 'Lax',
}
```

### 4. Configure SimpleJWT (optional)

```python title="settings.py"
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

!!! tip "Token Blacklisting"
    To enable token blacklisting on logout, add `'rest_framework_simplejwt.token_blacklist'` to `INSTALLED_APPS` and run migrations.

You now have JWT-specific endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/token/verify/` | POST | Verify JWT is valid |
| `/api/auth/token/refresh/` | POST | Refresh access token |

---

## Complete Example

Here's a complete configuration with all features enabled:

```python title="settings.py"
from datetime import timedelta

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    # dj-rest-auth
    'dj_rest_auth',
    'dj_rest_auth.registration',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

SITE_ID = 1

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
    ],
}

REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'access-token',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh-token',
    'JWT_AUTH_HTTPONLY': True,
    'JWT_AUTH_SECURE': False,  # Set True in production
    'JWT_AUTH_SAMESITE': 'Lax',
    'JWT_AUTH_RETURN_EXPIRATION': True,
    'SESSION_LOGIN': False,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Allauth configuration
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
```

```python title="urls.py"
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
]
```

---

## Next Steps

- [Quickstart Guide](quickstart.md) - Build a working example in 5 minutes
- [API Endpoints](../api/endpoints.md) - Complete endpoint reference
- [Configuration](../configuration/settings.md) - All available settings
