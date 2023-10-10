# Dj-Rest-Auth
Drop-in API endpoints for handling authentication securely in Django Rest Framework. Works especially well 
with SPAs (e.g., React, Vue, Angular), and Mobile applications.

  _This fork has implemented the Proof Key for Code Exchange (PKCE) protocol for enhanced security during OAuth 2.0 authentication flows. It is especially important for public clients like Single Page Applications and mobile apps.  Upstream attempts to integarte this important security enhancement have been [rejected by the maintainer](https://github.com/iMerica/dj-rest-auth/pull/470)._

Furthe PKCE Reading: https://curity.io/resources/learn/oauth-pkce/


## Why is PKCE Important?

* **Protect Against Authorization Code Interception:** PKCE was designed primarily to prevent an attacker from intercepting the authorization code in a public client, where the client secret cannot be kept confidential (like mobile or single-page applications).

* **No Fixed Client Secret:** Public clients, which can't maintain the confidentiality of a client secret, use PKCE to dynamically generate a secret for each authorization request. This ensures that even if an authorization code is intercepted, it cannot be used without the original secret created by the client.

* **Mitigate Man-in-the-Middle Attacks:** Without PKCE, if an attacker intercepts the authorization code, they might exploit it to obtain an access token. With PKCE, even if they have the code, they wouldn't have the necessary code_verifier to get the token.

* **Industry Recommendation:** Many industry experts and standards, including OAuth 2.0 for Native Apps (RFC 8252), recommend using PKCE, especially for public clients.

## Requirements
- Django 2, 3, or 4 (See Unit Test Coverage in CI)
- Python 3

## Quick Setup

Install package

    pip install dj-rest-auth
    
Add `dj_rest_auth` app to INSTALLED_APPS in your django settings.py:

```python
INSTALLED_APPS = (
    ...,
    'rest_framework',
    'rest_framework.authtoken',
    ...,
    'dj_rest_auth'
)
```
    
Add URL patterns

```python
urlpatterns = [
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
]
```
    

(Optional) Use Http-Only cookies

```python
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'jwt-auth',
}
```

### Testing

Install required modules with `pip install -r  dj_rest_auth/tests/requirements.pip`

To run the tests within a virtualenv, run `python runtests.py` from the repository directory.
The easiest way to run test coverage is with [`coverage`](https://pypi.org/project/coverage/),
which runs the tests against all supported Django installs. To run the test coverage 
within a virtualenv, run `coverage run ./runtests.py` from the repository directory then run `coverage report`.

#### Tox

Testing may also be done using [`tox`](https://pypi.org/project/tox/), which
will run the tests against all supported combinations of Python and Django.

Install tox, either globally or within a virtualenv, and then simply run `tox`
from the repository directory. As there are many combinations, you may run them
in [`parallel`](https://tox.readthedocs.io/en/latest/config.html#cmdoption-tox-p)
using `tox --parallel`.

The `tox.ini` includes an environment for testing code [`coverage`](https://pypi.org/project/coverage/)
and you can run it and view this report with `tox -e coverage`.

Linting may also be performed via [`flake8`](https://pypi.org/project/flake8/)
by running `tox -e flake8`.

### Documentation

View the full documentation here: https://dj-rest-auth.readthedocs.io/en/latest/index.html


### Acknowledgements

This project began as a fork of `django-rest-auth`. Big thanks to everyone who contributed to that repo!

