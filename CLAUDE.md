# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

dj-rest-auth is a Django REST Framework package providing authentication API endpoints (login, logout, registration, password reset/change, JWT auth). It integrates with django-allauth for social auth and registration.

## Common Commands

### Running Tests
```bash
# All tests
python runtests.py

# Single test
DJANGO_SETTINGS_MODULE=dj_rest_auth.tests.settings python -m django test dj_rest_auth.tests.test_api.APIBasicTests.test_login

# With coverage
coverage run ./runtests.py && coverage report
```

### Linting
```bash
flake8 dj_rest_auth/
```

### Tox (full CI matrix: Python 3.8-3.12, Django 4.2/5.0)
```bash
tox                  # all envs
tox -e flake8        # lint only
tox -e coverage      # coverage only
```

### Install Test Dependencies
```bash
pip install -r dj_rest_auth/tests/requirements.txt
```

## Architecture

### Core Package (`dj_rest_auth/`)

- **`app_settings.py`** — Central configuration via `REST_AUTH` Django setting dict. All serializers and the token model are specified as dotted import strings, making everything overridable without subclassing. Access settings via the `api_settings` singleton.
- **`views.py`** — `LoginView`, `LogoutView`, `UserDetailsView`, `PasswordResetView`, `PasswordResetConfirmView`, `PasswordChangeView`. All views use `throttle_scope = 'dj_rest_auth'`.
- **`serializers.py`** — Core serializers for all auth operations.
- **`jwt_auth.py`** — `JWTCookieAuthentication` (subclasses simplejwt's `JWTAuthentication`), cookie helpers, refresh view factory. Only active when `USE_JWT=True`.
- **`urls.py`** — Uses `re_path` with trailing `/?` to make slashes optional. JWT endpoints conditionally registered.
- **`models.py`** — No custom models; resolves and re-exports the configured Token model via `get_token_model()`.

### Registration Sub-package (`dj_rest_auth/registration/`)

Requires django-allauth. Provides `RegisterView`, `VerifyEmailView`, social login/connect views, and corresponding serializers.

### Key Design Patterns

- **Conditional allauth integration**: Checks `'allauth' in settings.INSTALLED_APPS` at runtime to branch between allauth and plain Django auth.
- **Settings-as-import-strings**: Serializers, token model, and token creator are all configurable via dotted path strings in `REST_AUTH`.
- **Custom validation hooks**: `custom_validation()` methods on password serializers for subclass extension.
- **i18n**: All user-facing strings use `gettext_lazy`.

### Testing (`dj_rest_auth/tests/`)

- **`settings.py`** — Test Django settings (SQLite in-memory, allauth configured).
- **`mixins.py`** — `TestsMixin` with HTTP helpers and status assertions; custom `APIClient`.
- **`utils.py`** — `override_api_settings` context manager for temporarily changing `REST_AUTH` values in tests.
- Test files: `test_api.py`, `test_serializers.py`, `test_social.py`, `test_utils.py`.

## Code Style

- flake8 with max line length 120 (configured in `setup.cfg`)
- `F403` (star imports) ignored globally
