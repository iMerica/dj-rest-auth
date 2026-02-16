MFA (Multi-Factor Authentication)
==================================

dj-rest-auth provides optional TOTP-based Multi-Factor Authentication (MFA) with backup recovery codes. When enabled, users must provide a time-based one-time password from an authenticator app (such as Google Authenticator, Authy, or 1Password) in addition to their username and password.

Features
--------

- **TOTP Authentication**: Industry-standard Time-based One-Time Passwords (RFC 6238)
- **Recovery Codes**: Backup codes for account recovery if the authenticator device is lost
- **Optional QR Code Generation**: Server can return QR SVG data URI for convenience
- **Customizable**: All serializers and settings are configurable

Installation
------------

Install MFA dependencies:

.. code-block:: bash

    pip install 'dj-rest-auth[with-mfa]'

.. note:: ``with-mfa`` installs TOTP support (``pyotp``). QR rendering remains optional.

1. Add ``dj_rest_auth.mfa`` to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = (
        ...,
        'rest_framework',
        'rest_framework.authtoken',
        'dj_rest_auth',
        'dj_rest_auth.mfa',  # Add this line
    )

2. Run migrations to create the ``Authenticator`` model:

.. code-block:: bash

    python manage.py migrate

3. Configure your URLs to use the MFA-enabled login view and include MFA endpoints:

.. code-block:: python

    from django.urls import path, include
    from dj_rest_auth.mfa.views import MFALoginView

    urlpatterns = [
        # Override the default login with MFA-enabled login
        path('dj-rest-auth/login/', MFALoginView.as_view(), name='rest_login'),
        # Include standard dj-rest-auth URLs
        path('dj-rest-auth/', include('dj_rest_auth.urls')),
        # Include MFA-specific URLs
        path('dj-rest-auth/', include('dj_rest_auth.mfa.urls')),
    ]

4. (Optional) Install ``qrcode`` for server-side QR code generation during TOTP setup:

.. code-block:: bash

    pip install qrcode

.. note:: Without ``qrcode``, the activation endpoint still works and returns ``totp_url`` + ``activation_token``.
   In headless/API-first clients, generating a QR client-side from ``totp_url`` is typically preferred.


Login Flow with MFA
-------------------

When a user has MFA enabled, the authentication flow changes:

1. **Initial Login**: Client sends username/password to the login endpoint
2. **Ephemeral Token**: If MFA is enabled, the server returns an ``ephemeral_token`` and ``mfa_required: true`` instead of completing authentication
3. **MFA Verification**: Client sends the ``ephemeral_token`` plus a valid TOTP code (or recovery code) to ``/mfa/verify/``
4. **Authentication Complete**: Server validates the code and returns the actual auth token (JWT or session-based)

.. code-block:: text

    ┌────────┐                    ┌─────────────────┐                    ┌────────────┐
    │ Client │                    │ Login Endpoint  │                    │ MFA Verify │
    └───┬────┘                    └────────┬────────┘                    └─────┬──────┘
        │                                  │                                   │
        │  POST {username, password}       │                                   │
        │─────────────────────────────────>│                                   │
        │                                  │                                   │
        │  {ephemeral_token, mfa_required} │                                   │
        │<─────────────────────────────────│                                   │
        │                                  │                                   │
        │  POST {ephemeral_token, code}                                        │
        │─────────────────────────────────────────────────────────────────────>│
        │                                                                      │
        │  {access_token, refresh_token}                                       │
        │<─────────────────────────────────────────────────────────────────────│


API Endpoints
-------------

MFA Verify
^^^^^^^^^^

- **/dj-rest-auth/mfa/verify/** (POST)

    Exchange an ephemeral token and TOTP/recovery code for a real auth token.

    **Request:**

    - ``ephemeral_token`` - Token received from login when MFA is required
    - ``code`` - TOTP code from authenticator app OR a recovery code

    **Response:** Same as standard login response (token, user details, etc.)

    .. note:: The ephemeral token expires after ``MFA_EPHEMERAL_TOKEN_TIMEOUT`` seconds (default: 300).


TOTP Activate
^^^^^^^^^^^^^

- **/dj-rest-auth/mfa/totp/activate/** (GET)

    Initialize TOTP setup. Returns a secret and provisioning URI for the authenticator app.

    **Response:**

    - ``secret`` - Base32-encoded TOTP secret (for manual app entry if needed)
    - ``totp_url`` - otpauth:// URI for authenticator apps (can be used by clients to render QR)
    - ``qr_code_data_uri`` - SVG QR code as a data URI (requires ``qrcode`` package)
    - ``activation_token`` - Signed token binding the secret to this user and request window

    .. note:: Requires authentication.

- **/dj-rest-auth/mfa/totp/activate/** (POST)

    Confirm TOTP activation with a valid code.

    **Request:**

    - ``activation_token`` - The signed activation token from the GET response
    - ``code`` - A valid TOTP code from the authenticator app

    **Response:**

    - ``recovery_codes`` - List of one-time recovery codes (save these!)

    .. note:: Requires authentication. Recovery codes are generated automatically upon TOTP activation.


TOTP Deactivate
^^^^^^^^^^^^^^^

- **/dj-rest-auth/mfa/totp/deactivate/** (POST)

    Deactivate TOTP MFA. Requires a valid TOTP code to confirm.

    **Request:**

    - ``code`` - A valid TOTP code

    **Response:**

    - ``detail`` - "TOTP has been deactivated."

    .. note:: Requires authentication. This also invalidates all recovery codes.


MFA Status
^^^^^^^^^^

- **/dj-rest-auth/mfa/status/** (GET)

    Check whether the current user has MFA enabled.

    **Response:**

    - ``mfa_enabled`` - Boolean indicating if MFA is active
    - ``created_at`` - Timestamp when MFA was activated (or null)
    - ``last_used_at`` - Timestamp of last successful MFA verification (or null)

    .. note:: Requires authentication.


Recovery Codes
^^^^^^^^^^^^^^

- **/dj-rest-auth/mfa/recovery-codes/** (GET)

    View unused recovery codes.

    **Response:**

    - ``codes`` - List of unused recovery codes

    .. note:: Requires authentication. Only shows codes that haven't been used yet.

- **/dj-rest-auth/mfa/recovery-codes/regenerate/** (POST)

    Regenerate recovery codes. Invalidates all previous codes.

    **Response:**

    - ``codes`` - List of new recovery codes

    .. note:: Requires authentication and MFA to be enabled. Previous recovery codes become invalid.


Recovery Codes
--------------

Recovery codes provide a backup method to access your account if you lose your authenticator device. Each code can only be used once.

**Best Practices:**

- Store recovery codes in a secure location (password manager, printed copy in a safe)
- Each code is formatted as ``xxxx-xxxx`` for easy reading
- The default count is 10 codes (configurable via ``MFA_RECOVERY_CODE_COUNT``)
- Regenerate codes periodically or when running low on unused codes
- Recovery codes are invalidated when TOTP is deactivated


Configuration
-------------

MFA behavior can be customized through the ``REST_AUTH`` settings dictionary:

.. code-block:: python

    REST_AUTH = {
        # MFA Settings
        'MFA_EPHEMERAL_TOKEN_TIMEOUT': 300,  # seconds
        'MFA_TOTP_DIGITS': 6,
        'MFA_TOTP_PERIOD': 30,  # seconds
        'MFA_TOTP_ISSUER': 'MyApp',
        'MFA_RECOVERY_CODE_COUNT': 10,

        # MFA Serializers (for customization)
        'MFA_VERIFY_SERIALIZER': 'dj_rest_auth.mfa.serializers.MFAVerifySerializer',
        'MFA_TOTP_ACTIVATE_INIT_SERIALIZER': 'dj_rest_auth.mfa.serializers.TOTPActivateInitSerializer',
        'MFA_TOTP_ACTIVATE_CONFIRM_SERIALIZER': 'dj_rest_auth.mfa.serializers.TOTPActivateConfirmSerializer',
        'MFA_TOTP_DEACTIVATE_SERIALIZER': 'dj_rest_auth.mfa.serializers.TOTPDeactivateSerializer',
        'MFA_STATUS_SERIALIZER': 'dj_rest_auth.mfa.serializers.MFAStatusSerializer',
        'MFA_RECOVERY_CODES_SERIALIZER': 'dj_rest_auth.mfa.serializers.RecoveryCodesSerializer',
    }


Setting Reference
^^^^^^^^^^^^^^^^^

``MFA_EPHEMERAL_TOKEN_TIMEOUT``
    Time in seconds before the ephemeral token expires. Default: ``300`` (5 minutes).

``MFA_TOTP_DIGITS``
    Number of digits in the TOTP code. Default: ``6``.

``MFA_TOTP_PERIOD``
    Time period in seconds for TOTP code validity. Default: ``30``.

``MFA_TOTP_ISSUER``
    Issuer name displayed in authenticator apps. Default: ``''`` (empty).

``MFA_RECOVERY_CODE_COUNT``
    Number of recovery codes to generate. Default: ``10``.


Example: Full MFA Setup Flow
----------------------------

Here's a complete example of setting up MFA for a user:

.. code-block:: python

    import requests

    BASE_URL = 'http://localhost:8000/dj-rest-auth'
    
    # 1. Login to get auth token (assuming MFA not yet enabled)
    response = requests.post(f'{BASE_URL}/login/', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    token = response.json()['key']  # or 'access' for JWT
    headers = {'Authorization': f'Token {token}'}
    
    # 2. Initialize TOTP setup
    response = requests.get(f'{BASE_URL}/mfa/totp/activate/', headers=headers)
    setup_data = response.json()
    print(f"Secret: {setup_data['secret']}")
    activation_token = setup_data['activation_token']
    print(f"Scan QR or enter secret in authenticator app")
    
    # 3. Get TOTP code from authenticator app and confirm activation
    totp_code = input("Enter TOTP code from app: ")
    response = requests.post(f'{BASE_URL}/mfa/totp/activate/', headers=headers, json={
        'activation_token': activation_token,
        'code': totp_code
    })
    recovery_codes = response.json()['recovery_codes']
    print(f"Save these recovery codes: {recovery_codes}")
    
    # 4. Now future logins require MFA
    response = requests.post(f'{BASE_URL}/login/', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    assert response.json()['mfa_required'] == True
    ephemeral_token = response.json()['ephemeral_token']
    
    # 5. Complete login with TOTP code
    totp_code = input("Enter TOTP code: ")
    response = requests.post(f'{BASE_URL}/mfa/verify/', json={
        'ephemeral_token': ephemeral_token,
        'code': totp_code
    })
    final_token = response.json()['key']  # Authenticated!
