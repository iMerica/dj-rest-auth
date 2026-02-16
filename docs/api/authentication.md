# Authentication Methods

dj-rest-auth supports multiple authentication methods. This guide explains how each works and when to use them.

## Overview

```mermaid
flowchart TD
    subgraph methods [Authentication Methods]
        Token[Token Auth]
        JWT[JWT Auth]
        Session[Session Auth]
    end
    
    subgraph storage [Client Storage]
        LocalStorage[localStorage/Memory]
        Cookies[HTTP-only Cookies]
        SessionCookie[Session Cookie]
    end
    
    Token --> LocalStorage
    JWT --> Cookies
    JWT --> LocalStorage
    Session --> SessionCookie
```

| Method | Best For | Storage | CSRF Protection |
|--------|----------|---------|-----------------|
| **Token Auth** | Mobile apps, simple APIs | Client-managed | Not needed |
| **JWT Cookies** | SPAs (React, Vue) | HTTP-only cookies | Built-in |
| **JWT Bearer** | Mobile apps, microservices | Client-managed | Not needed |
| **Session** | Traditional web apps | Session cookie | Django CSRF |

---

## Token Authentication

The simplest method. Django REST Framework's built-in token auth.

### How It Works

```mermaid
sequenceDiagram
    participant Client
    participant API as dj-rest-auth
    participant DB as Database
    
    Client->>API: POST /login/ {credentials}
    API->>DB: Validate user
    DB-->>API: User object
    API->>DB: Create/Get Token
    DB-->>API: Token key
    API-->>Client: {"key": "abc123..."}
    
    Note over Client: Store token in memory/localStorage
    
    Client->>API: GET /user/ with Token header
    API->>DB: Lookup token
    DB-->>API: User object
    API-->>Client: User data
```

### Configuration

```python title="settings.py"
INSTALLED_APPS = [
    # ...
    'rest_framework.authtoken',
    'dj_rest_auth',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

### Usage

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

**Authenticated Request:**
```bash
curl http://localhost:8000/api/auth/user/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

### Pros & Cons

| Pros | Cons |
|------|------|
| Simple to implement | Token never expires by default |
| Works everywhere | One token per user (no multiple sessions) |
| No external dependencies | Stored in database (DB lookup per request) |

---

## JWT Authentication

JSON Web Tokens with optional HTTP-only cookie storage. Recommended for SPAs.

### How It Works

```mermaid
sequenceDiagram
    participant Browser as Browser/SPA
    participant API as dj-rest-auth
    participant JWT as SimpleJWT
    
    Browser->>API: POST /login/ {credentials}
    API->>API: Validate user
    API->>JWT: Generate tokens
    JWT-->>API: Access + Refresh tokens
    API-->>Browser: Set-Cookie with HttpOnly tokens
    
    Note over Browser: Cookies stored automatically
    
    Browser->>API: GET /user/ with cookies
    API->>JWT: Validate access token
    JWT-->>API: Token valid, user_id=1
    API-->>Browser: User data
    
    Note over Browser: Access token expires...
    
    Browser->>API: POST /token/refresh/ with cookie
    API->>JWT: Validate refresh, generate new access
    JWT-->>API: New access token
    API-->>Browser: Set-Cookie with new access token
```

### Configuration

```python title="settings.py"
from datetime import timedelta

INSTALLED_APPS = [
    # ...
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # For logout
    'dj_rest_auth',
]

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
    'JWT_AUTH_SECURE': True,  # HTTPS only in production
    'JWT_AUTH_SAMESITE': 'Lax',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

### Cookie vs Bearer

dj-rest-auth supports both cookie-based and header-based JWT authentication simultaneously.

=== "Cookie (Recommended for SPAs)"

    Tokens are stored in HTTP-only cookies and sent automatically with every request.

    ```javascript
    // Login - cookies set automatically
    await fetch('/api/auth/login/', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    // Authenticated request - cookies sent automatically
    await fetch('/api/auth/user/', {
      credentials: 'include'
    });
    ```

=== "Bearer Header (Mobile/Microservices)"

    Store tokens yourself and send in Authorization header.

    ```python
    import requests

    # Login
    response = requests.post('/api/auth/login/', json={
        'username': 'user',
        'password': 'pass'
    })
    access_token = response.json()['access']

    # Authenticated request
    response = requests.get('/api/auth/user/', headers={
        'Authorization': f'Bearer {access_token}'
    })
    ```

### Pros & Cons

| Pros | Cons |
|------|------|
| Stateless (no DB lookup) | More complex setup |
| Automatic expiration | Requires refresh token handling |
| HTTP-only cookies prevent XSS | Larger request size |
| Works across subdomains | Token revocation requires blacklist |

---

## Session Authentication

Django's built-in session authentication. Best for traditional server-rendered apps.

### How It Works

```mermaid
sequenceDiagram
    participant Browser
    participant API as dj-rest-auth
    participant Session as Session Store
    
    Browser->>API: POST /login/ {credentials}
    API->>API: Validate user
    API->>Session: Create session
    Session-->>API: session_id
    API-->>Browser: Set-Cookie: sessionid=abc123
    
    Browser->>API: GET /user/ with session cookie
    API->>Session: Lookup session
    Session-->>API: User data
    API-->>Browser: {"username": "..."}
```

### Configuration

```python title="settings.py"
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
}

REST_AUTH = {
    'SESSION_LOGIN': True,
    'USE_JWT': False,
    'TOKEN_MODEL': None,  # Disable token auth
}
```

### Pros & Cons

| Pros | Cons |
|------|------|
| Built into Django | Requires CSRF protection |
| Easy session management | Stateful (server-side storage) |
| Works with Django admin | Doesn't scale horizontally easily |

---

## Combining Authentication Methods

You can enable multiple authentication methods:

```python title="settings.py"
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',  # JWT cookies
        'rest_framework.authentication.TokenAuthentication',  # Token header
        'rest_framework.authentication.SessionAuthentication',  # Session
    ],
}

REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'access',
    'SESSION_LOGIN': True,  # Also create session on login
}
```

This allows:
- Browser SPAs to use JWT cookies
- Mobile apps to use Token or JWT Bearer
- Admin users to use session auth

---

## Security Considerations

### CSRF Protection

| Method | CSRF Required | Notes |
|--------|--------------|-------|
| Token (Header) | No | Header-based auth is CSRF-immune |
| JWT (Header) | No | Header-based auth is CSRF-immune |
| JWT (Cookie) | Optional | Enable with `JWT_AUTH_COOKIE_USE_CSRF` |
| Session | Yes | Django CSRF middleware handles it |

### Token Storage

!!! danger "Never Store in localStorage"
    For SPAs, **never** store tokens in `localStorage` or `sessionStorage`. These are vulnerable to XSS attacks.

!!! success "Use HTTP-only Cookies"
    HTTP-only cookies cannot be accessed by JavaScript, preventing XSS token theft.

```python
REST_AUTH = {
    'JWT_AUTH_HTTPONLY': True,  # Prevent JS access
    'JWT_AUTH_SECURE': True,     # HTTPS only
    'JWT_AUTH_SAMESITE': 'Lax',  # CSRF protection
}
```

### Password Hashing

dj-rest-auth uses Django's password hashing system. Ensure you have strong hashers configured:

```python title="settings.py"
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]
```

---

## Decision Guide

```mermaid
flowchart TD
    Start[What are you building?] --> SPA{Single Page App?}
    Start --> Mobile{Mobile App?}
    Start --> Traditional{Server-rendered?}
    
    SPA -->|Yes| JWTCookie[Use JWT + HTTP-only Cookies]
    Mobile -->|Yes| JWTBearer[Use JWT Bearer or Token]
    Traditional -->|Yes| Session[Use Session Auth]
    
    JWTCookie --> Done[Configure REST_AUTH with USE_JWT=True]
    JWTBearer --> Done
    Session --> Done
```

| If you're building... | Use... | Why |
|----------------------|--------|-----|
| React/Vue/Angular SPA | JWT + Cookies | XSS protection, automatic handling |
| Mobile app | JWT Bearer or Token | Simple, stateless |
| Microservices | JWT Bearer | Stateless, scalable |
| Django templates + API | Session | Integrated with Django |
| Multiple client types | All methods | Maximum flexibility |
