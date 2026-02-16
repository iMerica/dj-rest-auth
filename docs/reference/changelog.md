# Changelog

All notable changes to dj-rest-auth are documented in this file.

For the full release history, see [GitHub Releases](https://github.com/iMerica/dj-rest-auth/releases).

## Version 7.x

### 7.1.0

- Latest stable release
- See [GitHub Release](https://github.com/iMerica/dj-rest-auth/releases/tag/v7.1.0) for details

### 7.0.0

**Breaking Changes:**

- Minimum Django version is now 4.2
- Minimum Python version is now 3.10
- Updated django-allauth compatibility

## Version 6.x

### 6.0.0

**Breaking Changes:**

- Dropped support for Django 3.x
- Updated SimpleJWT compatibility

## Version 5.x

### 5.0.0

**Breaking Changes:**

- JWT authentication is now handled by djangorestframework-simplejwt
- Removed django-rest-framework-jwt support (deprecated library)

## Version 4.x

### 4.0.0

**Features:**

- Added `JWT_AUTH_COOKIE_DOMAIN` setting
- Improved JWT cookie handling

## Version 3.x

### 3.0.0

**Breaking Changes:**

- All settings moved to `REST_AUTH` dictionary
- Renamed several settings for consistency

**Migration from 2.x:**

```python
# Old (2.x)
REST_USE_JWT = True
JWT_AUTH_COOKIE = 'my-cookie'

# New (3.x+)
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'my-cookie',
}
```

## Version 2.x

### 2.0.0

**Breaking Changes:**

- Renamed from `django-rest-auth` to `dj-rest-auth`
- Package name changed: `rest_auth` → `dj_rest_auth`

**Migration from django-rest-auth:**

1. Uninstall old package: `pip uninstall django-rest-auth`
2. Install new package: `pip install dj-rest-auth`
3. Update imports: `rest_auth` → `dj_rest_auth`
4. Update INSTALLED_APPS: `'rest_auth'` → `'dj_rest_auth'`

## Version 1.x

### 1.0.0

- Initial release as dj-rest-auth (fork of django-rest-auth)
- Added JWT support via djangorestframework-simplejwt
- Full Django 3.x support

---

## Deprecation Policy

- Major versions may include breaking changes
- Minor versions are backwards compatible
- Security fixes are backported to the latest major version
- Deprecated features are removed in the next major version
