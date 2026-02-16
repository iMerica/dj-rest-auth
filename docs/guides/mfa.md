# Multi-Factor Authentication (MFA)

dj-rest-auth includes optional TOTP-based MFA with one-time recovery codes. When enabled, users complete login with a second factor from an authenticator app.

## Overview

- **TOTP Authentication**: RFC 6238 time-based one-time passwords
- **Recovery Codes**: backup access if authenticator device is unavailable
- **Headless-first**: clients can render QR codes from `totp_url`
- **Optional server-side QR**: API can return `qr_code_data_uri` when `qrcode` is installed

## Setup

### 1) Install MFA extras

```bash
pip install 'dj-rest-auth[with-mfa]'
```

`with-mfa` installs TOTP support (`pyotp`).

### 2) Enable app

```python title="settings.py"
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'dj_rest_auth.mfa',
]
```

### 3) Run migrations

```bash
python manage.py migrate
```

### 4) Use MFA login view and include MFA URLs

```python title="urls.py"
from django.urls import include, path
from dj_rest_auth.mfa.views import MFALoginView

urlpatterns = [
    path('dj-rest-auth/login/', MFALoginView.as_view(), name='rest_login'),
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/', include('dj_rest_auth.mfa.urls')),
]
```

### Optional: server-side QR rendering

```bash
pip install qrcode
```

!!! note
    Without `qrcode`, activation still works. Clients can generate a QR code from `totp_url`.

## Login flow

When MFA is enabled for a user:

1. Client sends username/password to login endpoint.
2. API returns `ephemeral_token` + `mfa_required: true` (instead of full login).
3. Client submits `ephemeral_token` + TOTP (or recovery code) to MFA verify endpoint.
4. API returns normal auth response (token/JWT/session login).

## Endpoints

### Verify MFA

`POST /dj-rest-auth/mfa/verify/`

Request fields:

- `ephemeral_token`
- `code` (TOTP or recovery code)

### Activate TOTP (step 1)

`GET /dj-rest-auth/mfa/totp/activate/`

Response fields:

- `secret`
- `totp_url`
- `activation_token`
- `qr_code_data_uri` (empty string when `qrcode` is not installed)

### Activate TOTP (step 2)

`POST /dj-rest-auth/mfa/totp/activate/`

Request fields:

- `activation_token`
- `code`

Response fields:

- `recovery_codes`

### Deactivate TOTP

`POST /dj-rest-auth/mfa/totp/deactivate/`

Request fields:

- `code`

Response:

- `detail`

### Status

`GET /dj-rest-auth/mfa/status/`

Response fields:

- `mfa_enabled`
- `created_at`
- `last_used_at`

### Recovery codes

- `GET /dj-rest-auth/mfa/recovery-codes/` (list unused codes)
- `POST /dj-rest-auth/mfa/recovery-codes/regenerate/` (rotate all codes)

## Security behavior

- `ephemeral_token` expires after `MFA_EPHEMERAL_TOKEN_TIMEOUT` (default 300s)
- activation requires a signed, user-bound `activation_token`
- recovery code usage is atomic and one-time
- sensitive MFA events are logged via `dj_rest_auth.mfa` logger

## Settings

Configure via `REST_AUTH`:

```python title="settings.py"
REST_AUTH = {
    'MFA_EPHEMERAL_TOKEN_TIMEOUT': 300,
    'MFA_TOTP_DIGITS': 6,
    'MFA_TOTP_PERIOD': 30,
    'MFA_TOTP_ISSUER': '',
    'MFA_RECOVERY_CODE_COUNT': 10,
}
```
