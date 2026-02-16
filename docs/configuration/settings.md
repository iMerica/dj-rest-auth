# Settings Reference

All dj-rest-auth settings are configured in the `REST_AUTH` dictionary in your Django settings.

```python title="settings.py"
REST_AUTH = {
    'LOGIN_SERIALIZER': 'dj_rest_auth.serializers.LoginSerializer',
    'USE_JWT': False,
    # ... more settings
}
```

---

## Serializer Settings

These settings allow you to replace default serializers with custom ones.

### LOGIN_SERIALIZER

Path to the serializer class used in `LoginView`.

| | |
|---|---|
| **Default** | `'dj_rest_auth.serializers.LoginSerializer'` |
| **Type** | String (dotted import path) |

```python
REST_AUTH = {
    'LOGIN_SERIALIZER': 'myapp.serializers.CustomLoginSerializer',
}
```

---

### TOKEN_SERIALIZER

Path to the serializer class for Token authentication responses.

| | |
|---|---|
| **Default** | `'dj_rest_auth.serializers.TokenSerializer'` |
| **Type** | String (dotted import path) |

!!! note
    Set to `None` together with `TOKEN_MODEL` if you don't want to use Token Authentication.

---

### JWT_SERIALIZER

Path to the serializer class for JWT responses (when `USE_JWT=True`).

| | |
|---|---|
| **Default** | `'dj_rest_auth.serializers.JWTSerializer'` |
| **Type** | String (dotted import path) |

---

### JWT_SERIALIZER_WITH_EXPIRATION

Path to the serializer class for JWT responses with expiration times (when `JWT_AUTH_RETURN_EXPIRATION=True`).

| | |
|---|---|
| **Default** | `'dj_rest_auth.serializers.JWTSerializerWithExpiration'` |
| **Type** | String (dotted import path) |

---

### JWT_TOKEN_CLAIMS_SERIALIZER

Path to the serializer class for JWT token claims.

| | |
|---|---|
| **Default** | `'rest_framework_simplejwt.serializers.TokenObtainPairSerializer'` |
| **Type** | String (dotted import path) |

Override this to add custom claims to your JWT tokens:

```python title="serializers.py"
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenClaimsSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        token['is_staff'] = user.is_staff
        return token
```

---

### USER_DETAILS_SERIALIZER

Path to the serializer class for `UserDetailsView`.

| | |
|---|---|
| **Default** | `'dj_rest_auth.serializers.UserDetailsSerializer'` |
| **Type** | String (dotted import path) |

```python title="serializers.py"
from dj_rest_auth.serializers import UserDetailsSerializer

class CustomUserDetailsSerializer(UserDetailsSerializer):
    class Meta(UserDetailsSerializer.Meta):
        fields = ('pk', 'username', 'email', 'first_name', 'last_name', 'profile_picture')
```

---

### PASSWORD_RESET_SERIALIZER

Path to the serializer class for `PasswordResetView`.

| | |
|---|---|
| **Default** | `'dj_rest_auth.serializers.PasswordResetSerializer'` |
| **Type** | String (dotted import path) |

---

### PASSWORD_RESET_CONFIRM_SERIALIZER

Path to the serializer class for `PasswordResetConfirmView`.

| | |
|---|---|
| **Default** | `'dj_rest_auth.serializers.PasswordResetConfirmSerializer'` |
| **Type** | String (dotted import path) |

---

### PASSWORD_CHANGE_SERIALIZER

Path to the serializer class for `PasswordChangeView`.

| | |
|---|---|
| **Default** | `'dj_rest_auth.serializers.PasswordChangeSerializer'` |
| **Type** | String (dotted import path) |

---

### REGISTER_SERIALIZER

Path to the serializer class for `RegisterView`.

| | |
|---|---|
| **Default** | `'dj_rest_auth.registration.serializers.RegisterSerializer'` |
| **Type** | String (dotted import path) |

!!! warning "Custom Serializer Requirement"
    Your custom `REGISTER_SERIALIZER` **must** define a `save(self, request)` method that returns a user model instance.

```python title="serializers.py"
from dj_rest_auth.registration.serializers import RegisterSerializer

class CustomRegisterSerializer(RegisterSerializer):
    phone_number = serializers.CharField(max_length=20, required=False)

    def custom_signup(self, request, user):
        user.profile.phone_number = self.validated_data.get('phone_number', '')
        user.profile.save()
```

---

## Permission Settings

### REGISTER_PERMISSION_CLASSES

Tuple of permission classes for `RegisterView`.

| | |
|---|---|
| **Default** | `('rest_framework.permissions.AllowAny',)` |
| **Type** | Tuple of strings (dotted import paths) |

```python
REST_AUTH = {
    'REGISTER_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
        'myapp.permissions.RegistrationRateLimit',
    ),
}
```

---

## Token Settings

### TOKEN_MODEL

Path to the model class for token authentication.

| | |
|---|---|
| **Default** | `'rest_framework.authtoken.models.Token'` |
| **Type** | String (dotted import path) or `None` |

Set to `None` to disable token authentication. When `None`, at least one of `SESSION_LOGIN` or `USE_JWT` must be `True`.

---

### TOKEN_CREATOR

Path to the callable that creates tokens.

| | |
|---|---|
| **Default** | `'dj_rest_auth.utils.default_create_token'` |
| **Type** | String (dotted import path) |

The callable signature: `create_token(token_model, user, serializer) -> token`

```python title="utils.py"
def custom_create_token(token_model, user, serializer):
    token, created = token_model.objects.get_or_create(user=user)
    if not created:
        # Refresh token on every login
        token.delete()
        token = token_model.objects.create(user=user)
    return token
```

---

## Behavior Settings

### PASSWORD_RESET_USE_SITES_DOMAIN

Use the domain from `django.contrib.sites` in password reset emails.

| | |
|---|---|
| **Default** | `False` |
| **Type** | Boolean |

When `True`, the domain in password reset emails will be taken from the Site with `SITE_ID=1`.

---

### OLD_PASSWORD_FIELD_ENABLED

Require old password when changing password.

| | |
|---|---|
| **Default** | `False` |
| **Type** | Boolean |

When `True`, the `old_password` field is required in `PasswordChangeView`.

---

### LOGOUT_ON_PASSWORD_CHANGE

Log out user after password change.

| | |
|---|---|
| **Default** | `False` |
| **Type** | Boolean |

When `True`, the user will be logged out after successfully changing their password.

---

### SESSION_LOGIN

Create Django session on login.

| | |
|---|---|
| **Default** | `True` |
| **Type** | Boolean |

When `True`, a Django session is created on login (in addition to token/JWT).

---

## JWT Settings

These settings only apply when `USE_JWT=True`.

### USE_JWT

Enable JWT authentication.

| | |
|---|---|
| **Default** | `False` |
| **Type** | Boolean |

When `True`, login returns JWT tokens instead of (or in addition to) DRF tokens.

!!! note "Dependency"
    Requires `djangorestframework-simplejwt` to be installed.

---

### JWT_AUTH_COOKIE

Cookie name for the access token.

| | |
|---|---|
| **Default** | `None` |
| **Type** | String or `None` |

When set, the access token is stored in an HTTP cookie with this name.

```python
REST_AUTH = {
    'JWT_AUTH_COOKIE': 'my-app-auth',
}
```

---

### JWT_AUTH_REFRESH_COOKIE

Cookie name for the refresh token.

| | |
|---|---|
| **Default** | `None` |
| **Type** | String or `None` |

When set, the refresh token is stored in an HTTP cookie with this name.

---

### JWT_AUTH_REFRESH_COOKIE_PATH

Cookie path for the refresh token.

| | |
|---|---|
| **Default** | `'/'` |
| **Type** | String |

Restrict the refresh token cookie to a specific path (e.g., `'/api/auth/token/refresh/'`).

---

### JWT_AUTH_SECURE

Only send cookies over HTTPS.

| | |
|---|---|
| **Default** | `False` |
| **Type** | Boolean |

!!! danger "Production Setting"
    **Always set to `True` in production** to prevent token theft over insecure connections.

---

### JWT_AUTH_HTTPONLY

Prevent JavaScript access to cookies.

| | |
|---|---|
| **Default** | `True` |
| **Type** | Boolean |

!!! warning "Security Implication"
    When `True`, the refresh token will not be included in the JSON response body (only in the cookie). Set to `False` only if you need to access tokens from JavaScript.

---

### JWT_AUTH_SAMESITE

SameSite attribute for cookies.

| | |
|---|---|
| **Default** | `'Lax'` |
| **Type** | String (`'Strict'`, `'Lax'`, `'None'`, or `False`) |

| Value | Behavior |
|-------|----------|
| `'Strict'` | Cookie only sent for same-site requests |
| `'Lax'` | Cookie sent for same-site and top-level navigations |
| `'None'` | Cookie sent for all requests (requires `JWT_AUTH_SECURE=True`) |
| `False` | Don't set SameSite attribute |

---

### JWT_AUTH_COOKIE_DOMAIN

Domain for JWT cookies.

| | |
|---|---|
| **Default** | `None` |
| **Type** | String or `None` |

Set this to share cookies across subdomains:

```python
REST_AUTH = {
    'JWT_AUTH_COOKIE_DOMAIN': '.example.com',  # Note the leading dot
}
```

---

### JWT_AUTH_RETURN_EXPIRATION

Include token expiration times in login response.

| | |
|---|---|
| **Default** | `False` |
| **Type** | Boolean |

When `True`, the login response includes `access_expiration` and `refresh_expiration` fields.

---

### JWT_AUTH_COOKIE_USE_CSRF

Enable CSRF protection for cookie-authenticated requests.

| | |
|---|---|
| **Default** | `False` |
| **Type** | Boolean |

When `True`, CSRF validation is required for authenticated views when using JWT cookies.

---

### JWT_AUTH_COOKIE_ENFORCE_CSRF_ON_UNAUTHENTICATED

Enable CSRF protection for all requests when using JWT cookies.

| | |
|---|---|
| **Default** | `False` |
| **Type** | Boolean |

When `True`, CSRF validation is required for all views (authenticated and unauthenticated).

---

## Complete Default Configuration

```python title="settings.py"
REST_AUTH = {
    # Serializers
    'LOGIN_SERIALIZER': 'dj_rest_auth.serializers.LoginSerializer',
    'TOKEN_SERIALIZER': 'dj_rest_auth.serializers.TokenSerializer',
    'JWT_SERIALIZER': 'dj_rest_auth.serializers.JWTSerializer',
    'JWT_SERIALIZER_WITH_EXPIRATION': 'dj_rest_auth.serializers.JWTSerializerWithExpiration',
    'JWT_TOKEN_CLAIMS_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer',
    'USER_DETAILS_SERIALIZER': 'dj_rest_auth.serializers.UserDetailsSerializer',
    'PASSWORD_RESET_SERIALIZER': 'dj_rest_auth.serializers.PasswordResetSerializer',
    'PASSWORD_RESET_CONFIRM_SERIALIZER': 'dj_rest_auth.serializers.PasswordResetConfirmSerializer',
    'PASSWORD_CHANGE_SERIALIZER': 'dj_rest_auth.serializers.PasswordChangeSerializer',
    'REGISTER_SERIALIZER': 'dj_rest_auth.registration.serializers.RegisterSerializer',
    
    # Permissions
    'REGISTER_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
    
    # Token
    'TOKEN_MODEL': 'rest_framework.authtoken.models.Token',
    'TOKEN_CREATOR': 'dj_rest_auth.utils.default_create_token',
    
    # Behavior
    'PASSWORD_RESET_USE_SITES_DOMAIN': False,
    'OLD_PASSWORD_FIELD_ENABLED': False,
    'LOGOUT_ON_PASSWORD_CHANGE': False,
    'SESSION_LOGIN': True,
    'USE_JWT': False,
    
    # JWT
    'JWT_AUTH_COOKIE': None,
    'JWT_AUTH_REFRESH_COOKIE': None,
    'JWT_AUTH_REFRESH_COOKIE_PATH': '/',
    'JWT_AUTH_SECURE': False,
    'JWT_AUTH_HTTPONLY': True,
    'JWT_AUTH_SAMESITE': 'Lax',
    'JWT_AUTH_COOKIE_DOMAIN': None,
    'JWT_AUTH_RETURN_EXPIRATION': False,
    'JWT_AUTH_COOKIE_USE_CSRF': False,
    'JWT_AUTH_COOKIE_ENFORCE_CSRF_ON_UNAUTHENTICATED': False,
}
```
