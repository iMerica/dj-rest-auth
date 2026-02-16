# Security

## Vulnerability Disclosure Policy

Please observe standard best practices of responsible disclosure when reporting security vulnerabilities.

See OWASP's [Vulnerability Disclosure Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Vulnerability_Disclosure_Cheat_Sheet.html) for guidance.

### Reporting a Vulnerability

1. **Do not** open a public GitHub issue for security vulnerabilities
2. **Email** the maintainer directly: [imichael@pm.me](mailto:imichael@pm.me)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- Acknowledgment within 48 hours
- Regular updates on progress
- Credit in the security advisory (unless you prefer anonymity)

### Guidelines

- **Keep it legal** - Only test against your own installations
- **Respect privacy** - Don't access or modify other users' data
- **Be patient** - Security fixes take time to develop and test properly

---

## Security Best Practices

### JWT Configuration

```python title="settings.py (Production)"
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'access',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh',
    'JWT_AUTH_HTTPONLY': True,       # Prevent XSS
    'JWT_AUTH_SECURE': True,          # HTTPS only
    'JWT_AUTH_SAMESITE': 'Lax',       # CSRF protection
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),   # Short-lived
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

### Rate Limiting

Protect against brute force attacks:

```python title="settings.py"
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'dj_rest_auth': '100/hour',
    },
}
```

### Password Validation

Use Django's password validators:

```python title="settings.py"
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

### HTTPS

Always use HTTPS in production:

```python title="settings.py"
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## Known Security Considerations

### Email Enumeration

By design, the password reset endpoint always returns a success response, even for non-existent emails. This prevents attackers from determining which emails are registered.

### Token Storage

- **DO**: Store tokens in HTTP-only cookies
- **DON'T**: Store tokens in localStorage or sessionStorage (XSS vulnerable)

### CORS

Be restrictive with CORS origins in production:

```python title="settings.py"
CORS_ALLOWED_ORIGINS = [
    'https://yourapp.com',  # Specific domains only
]
CORS_ALLOW_CREDENTIALS = True
```

---

## Security Updates

Security updates are released as patch versions. Always keep dj-rest-auth updated:

```bash
pip install --upgrade dj-rest-auth
```

Subscribe to [GitHub releases](https://github.com/iMerica/dj-rest-auth/releases) for security announcements.
