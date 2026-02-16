# Upgrade Guide

This guide helps you upgrade between major versions of dj-rest-auth.

## Upgrading to 7.x

### Requirements

- Python >= 3.10
- Django >= 4.2
- Django REST Framework >= 3.14

### Steps

1. Update your Python version if needed
2. Update Django: `pip install 'Django>=4.2'`
3. Update dj-rest-auth: `pip install 'dj-rest-auth>=7.0'`
4. Run tests to verify everything works

### Breaking Changes

- Dropped support for Python 3.8 and 3.9
- Dropped support for Django 4.0 and 4.1

---

## Upgrading to 6.x

### Requirements

- Python >= 3.8
- Django >= 4.0

### Breaking Changes

- Dropped support for Django 3.x

---

## Upgrading to 5.x (JWT Migration)

Version 5.0 switched from `django-rest-framework-jwt` to `djangorestframework-simplejwt`.

### Steps

1. Uninstall old JWT library:
   ```bash
   pip uninstall djangorestframework-jwt
   ```

2. Install SimpleJWT:
   ```bash
   pip install djangorestframework-simplejwt
   ```

3. Update settings:
   ```python
   # Old
   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': [
           'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
       ],
   }

   # New
   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': [
           'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
       ],
   }
   ```

4. Update JWT settings:
   ```python
   # Old (django-rest-framework-jwt)
   JWT_AUTH = {
       'JWT_EXPIRATION_DELTA': datetime.timedelta(days=7),
   }

   # New (djangorestframework-simplejwt)
   from datetime import timedelta
   SIMPLE_JWT = {
       'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
       'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
   }
   ```

---

## Upgrading to 3.x (Settings Migration)

Version 3.0 consolidated all settings into a single `REST_AUTH` dictionary.

### Steps

1. Move all settings into `REST_AUTH`:

   ```python
   # Old (2.x)
   REST_USE_JWT = True
   REST_SESSION_LOGIN = True
   JWT_AUTH_COOKIE = 'jwt-auth'
   JWT_AUTH_REFRESH_COOKIE = 'jwt-refresh'
   OLD_PASSWORD_FIELD_ENABLED = True

   # New (3.x)
   REST_AUTH = {
       'USE_JWT': True,
       'SESSION_LOGIN': True,
       'JWT_AUTH_COOKIE': 'jwt-auth',
       'JWT_AUTH_REFRESH_COOKIE': 'jwt-refresh',
       'OLD_PASSWORD_FIELD_ENABLED': True,
   }
   ```

2. Update any code referencing old settings:

   ```python
   # Old
   from django.conf import settings
   if settings.REST_USE_JWT:
       ...

   # New
   from dj_rest_auth.app_settings import api_settings
   if api_settings.USE_JWT:
       ...
   ```

### Settings Renamed

| Old Name | New Name |
|----------|----------|
| `REST_USE_JWT` | `USE_JWT` |
| `REST_SESSION_LOGIN` | `SESSION_LOGIN` |
| `OLD_PASSWORD_FIELD_ENABLED` | `OLD_PASSWORD_FIELD_ENABLED` |
| `LOGOUT_ON_PASSWORD_CHANGE` | `LOGOUT_ON_PASSWORD_CHANGE` |

---

## Upgrading from django-rest-auth

If you're migrating from the original `django-rest-auth` package:

### Steps

1. Uninstall the old package:
   ```bash
   pip uninstall django-rest-auth
   ```

2. Install dj-rest-auth:
   ```bash
   pip install dj-rest-auth
   ```

3. Update `INSTALLED_APPS`:
   ```python
   # Old
   INSTALLED_APPS = [
       'rest_auth',
       'rest_auth.registration',
   ]

   # New
   INSTALLED_APPS = [
       'dj_rest_auth',
       'dj_rest_auth.registration',
   ]
   ```

4. Update imports throughout your code:
   ```python
   # Old
   from rest_auth.views import LoginView
   from rest_auth.serializers import UserDetailsSerializer

   # New
   from dj_rest_auth.views import LoginView
   from dj_rest_auth.serializers import UserDetailsSerializer
   ```

5. Update URL includes:
   ```python
   # Old
   path('api/auth/', include('rest_auth.urls')),

   # New
   path('api/auth/', include('dj_rest_auth.urls')),
   ```

6. Run database migrations (if any):
   ```bash
   python manage.py migrate
   ```

### Find and Replace

Use your IDE's find and replace to update all occurrences:

| Find | Replace |
|------|---------|
| `rest_auth` | `dj_rest_auth` |
| `from rest_auth` | `from dj_rest_auth` |
| `'rest_auth'` | `'dj_rest_auth'` |

---

## Troubleshooting Upgrades

### Import Errors

If you see `ImportError: No module named 'rest_auth'`:
- You haven't updated all imports to `dj_rest_auth`
- Run: `grep -r "rest_auth" --include="*.py" .`

### Settings Errors

If you see `ImproperlyConfigured: The 'X' setting has been removed`:
- Check the [Settings Reference](../configuration/settings.md) for current settings
- Migrate old settings to the `REST_AUTH` dictionary

### Migration Errors

If you see database migration errors:
- Ensure all apps are in `INSTALLED_APPS`
- Run `python manage.py migrate --run-syncdb`
