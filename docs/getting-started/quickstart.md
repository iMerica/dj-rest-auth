# Quickstart

Build a working authentication API in 5 minutes.

## Prerequisites

- Python 3.10+
- Django 4.2+

## Step 1: Create a Django Project

```bash
# Create project directory
mkdir myproject && cd myproject

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install django djangorestframework dj-rest-auth

# Create Django project
django-admin startproject config .
```

## Step 2: Configure Settings

Edit `config/settings.py`:

```python title="config/settings.py"
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Add these
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
]

# Add at the bottom
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

## Step 3: Configure URLs

Edit `config/urls.py`:

```python title="config/urls.py"
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('dj_rest_auth.urls')),
]
```

## Step 4: Run Migrations

```bash
python manage.py migrate
```

## Step 5: Create a Test User

```bash
python manage.py createsuperuser --username testuser --email test@example.com
```

Enter a password when prompted.

## Step 6: Start the Server

```bash
python manage.py runserver
```

## Step 7: Test the API

### Login

=== "curl"

    ```bash
    curl -X POST http://localhost:8000/api/auth/login/ \
      -H "Content-Type: application/json" \
      -d '{"username": "testuser", "password": "yourpassword"}'
    ```

=== "httpie"

    ```bash
    http POST localhost:8000/api/auth/login/ \
      username=testuser password=yourpassword
    ```

=== "Python"

    ```python
    import requests

    response = requests.post(
        'http://localhost:8000/api/auth/login/',
        json={'username': 'testuser', 'password': 'yourpassword'}
    )
    print(response.json())
    ```

**Response:**

```json
{
    "key": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

### Get User Details

Use the token from the login response:

=== "curl"

    ```bash
    curl http://localhost:8000/api/auth/user/ \
      -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
    ```

=== "httpie"

    ```bash
    http localhost:8000/api/auth/user/ \
      "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
    ```

=== "Python"

    ```python
    import requests

    response = requests.get(
        'http://localhost:8000/api/auth/user/',
        headers={'Authorization': 'Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b'}
    )
    print(response.json())
    ```

**Response:**

```json
{
    "pk": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "",
    "last_name": ""
}
```

### Logout

=== "curl"

    ```bash
    curl -X POST http://localhost:8000/api/auth/logout/ \
      -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
    ```

=== "httpie"

    ```bash
    http POST localhost:8000/api/auth/logout/ \
      "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
    ```

**Response:**

```json
{
    "detail": "Successfully logged out."
}
```

---

## Adding JWT Authentication

Want to use JWT with HTTP-only cookies instead of token authentication? Here's how:

### 1. Install SimpleJWT

```bash
pip install djangorestframework-simplejwt
```

### 2. Update Settings

```python title="config/settings.py"
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
    ],
}

REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'access',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh',
    'JWT_AUTH_HTTPONLY': True,
}
```

### 3. Test JWT Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "yourpassword"}' \
  -c cookies.txt
```

The response now includes JWT tokens, and cookies are automatically set:

```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "",
    "user": {
        "pk": 1,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "",
        "last_name": ""
    }
}
```

### 4. Access Protected Endpoints

With cookies (browser-like behavior):

```bash
curl http://localhost:8000/api/auth/user/ -b cookies.txt
```

---

## Adding User Registration

### 1. Install allauth

```bash
pip install 'dj-rest-auth[with-social]'
```

### 2. Update Settings

```python title="config/settings.py"
INSTALLED_APPS = [
    # ... existing apps ...
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'dj_rest_auth.registration',
]

MIDDLEWARE = [
    # ... existing middleware ...
    'allauth.account.middleware.AccountMiddleware',
]

SITE_ID = 1

# Email verification (optional)
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Change to 'mandatory' for production
```

### 3. Update URLs

```python title="config/urls.py"
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
]
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Test Registration

```bash
curl -X POST http://localhost:8000/api/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "new@example.com",
    "password1": "complexpassword123",
    "password2": "complexpassword123"
  }'
```

**Response:**

```json
{
    "key": "a1b2c3d4e5f6g7h8i9j0..."
}
```

---

## Next Steps

- [API Endpoints](../api/endpoints.md) - Complete endpoint documentation
- [JWT & Cookies](../guides/jwt-cookies.md) - Deep dive into JWT configuration
- [Social Auth](../guides/social-auth.md) - Add Google, GitHub, etc.
- [Configuration](../configuration/settings.md) - All available settings
