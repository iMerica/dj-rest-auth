Configuration
=============

dj-rest-auth behaviour can be controlled by adjust settings in ``settings.py``:

.. code-block:: python

    # Django project settings.py

    ...

    REST_AUTH = {
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

        'REGISTER_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),

        'TOKEN_MODEL': 'rest_framework.authtoken.models.Token',
        'TOKEN_CREATOR': 'dj_rest_auth.utils.default_create_token',

        'PASSWORD_RESET_USE_SITES_DOMAIN': False,
        'OLD_PASSWORD_FIELD_ENABLED': False,
        'LOGOUT_ON_PASSWORD_CHANGE': False,
        'SESSION_LOGIN': True,
        'USE_JWT': False,

        'JWT_AUTH_COOKIE': None,
        'JWT_AUTH_REFRESH_COOKIE': None,
        'JWT_AUTH_REFRESH_COOKIE_PATH': '/',
        'JWT_AUTH_SECURE': False,
        'JWT_AUTH_HTTPONLY': True,
        'JWT_AUTH_SAMESITE': 'Lax',
        'JWT_AUTH_RETURN_EXPIRATION': False,
        'JWT_AUTH_COOKIE_USE_CSRF': False,
        'JWT_AUTH_COOKIE_ENFORCE_CSRF_ON_UNAUTHENTICATED': False,
    }

Above, the default values for these settings are shown.

``LOGIN_SERIALIZER``
====================

The path to the serializer class for the login in
``dj_rest_auth.views.LoginView``. The value is the dotted path to
``dj_rest_auth.serializers.LoginSerializer``, which is also the default.

``TOKEN_SERIALIZER``
====================

The path to the serializer class for the Token response on successful
authentication in ``dj_rest_auth.views.LoginView``. The value is the dotted
path to ``dj_rest_auth.serializers.TokenSerializer``, which is also the
default.

``JWT_SERIALIZER``
==================

The path to the serializer class for the JWT response on successful
authentication in ``dj_rest_auth.views.LoginView``. The value is the dotted
path to ``dj_rest_auth.serializers.JWTSerializer``, which is also the default.
Requires ``USE_JWT=True`` in settings.

``JWT_SERIALIZER_WITH_EXPIRATION``
==================================

The path to the serializer class for the JWT response with its expiration time
on successful authentication in ``dj_rest_auth.views.LoginView``. The value is
the dotted path to ``dj_rest_auth.serializers.JWTSerializerWithExpiration``,
which is also the default. Requires ``USE_JWT=True`` in settings.

``JWT_TOKEN_CLAIMS_SERIALIZER``
===============================

The path to the serializer class for the JWT Claims on successful
authentication in ``dj_rest_auth.views.LoginView``. The value is the dotted
path to ``rest_framework_simplejwt.serializers.TokenObtainPairSerializer``,
which is also the default. Requires ``USE_JWT=True`` in settings.

``USER_DETAILS_SERIALIZER``
===========================

The path to the serializer class for the User details in
``dj_rest_auth.views.UserDetailsView``. The value is the dotted path to
``dj_rest_auth.serializers.UserDetailsSerializer``, which is also the default.

``PASSWORD_RESET_SERIALIZER``
=============================

The path to the serializer class for the password reset in
``dj_rest_auth.views.PasswordResetView``. The value is the dotted path to
``dj_rest_auth.serializers.PasswordResetSerializer``, which is also the
default.

``PASSWORD_RESET_CONFIRM_SERIALIZER``
=====================================

The path to the serializer class for the password reset confirm in
``dj_rest_auth.views.PasswordResetConfirmView``. The value is the dotted path to
``dj_rest_auth.serializers.PasswordResetConfirmSerializer``, which is also the
default.

``PASSWORD_CHANGE_SERIALIZER``
==============================

The path to the serializer class for the password change in
``dj_rest_auth.views.PasswordChangeView``. The value is the dotted path to
``dj_rest_auth.serializers.PasswordChangeSerializer``, which is also the
default.

``REGISTER_SERIALIZER``
=======================

The path to the serializer class for the register in
``dj_rest_auth.registration.views.RegisterView``. The value is the dotted path
to ``dj_rest_auth.registration.serializers.RegisterSerializer``, which is also
the default.

.. note:: The custom ``REGISTER_SERIALIZER`` must define a ``def save(self, request)`` method that returns a user model instance.

``REGISTER_PERMISSION_CLASSES``
===============================

A tuple that contains paths to the permission classes for the register in
``dj_rest_auth.registration.views.RegisterView``. The value is the dotted path
to ``path.to.another.permission.class``.
``rest_framework.permissions.AllowAny`` is included by default.

``TOKEN_MODEL``
===============

The path to the model class for the token. The value is the dotted path to
``rest_framework.authtoken.models.Token``, which is also the default. If set to
``None`` token authentication will be disabled. In this case at least one of
``SESSION_LOGIN`` or ``USE_JWT`` must be enabled.

``TOKEN_CREATOR``
=================

The path to callable for creating tokens. The value is the dotted path to
``dj_rest_auth.utils.default_create_token``, which is also the default.

``PASSWORD_RESET_USE_SITES_DOMAIN``
===================================

If set to ``True``, the domain in the password reset e-mail will be set to the
domain you defined in ``django.contrib.sites`` module with ``SITE_ID=1``.
Default is ``False``.

``OLD_PASSWORD_FIELD_ENABLED``
==============================

If set to ``True``, old password verification in
``dj_rest_auth.views.PasswordChangeView`` will be added. Default is ``False``.

``LOGOUT_ON_PASSWORD_CHANGE``
=============================

If set to ``True``, current user will be logged out after a password change.
Default is ``False``.

``SESSION_LOGIN``
=================

If set to ``True``, session login in ``dj_rest_auth.views.LoginView`` will be
enabled. Default is ``True``.

``USE_JWT``
===========

If set to ``True``, JWT Authentication in ``dj_rest_auth.views.LoginView`` will
be used instead of Token or Session based login. Default is ``False``.

.. note:: JWT Authentication in dj-rest-auth is built on top of djangorestframework-simplejwt https://github.com/SimpleJWT/django-rest-framework-simplejwt. You must install it in order to be able to use JWT Authentication in dj-rest-auth.

``JWT_AUTH_COOKIE``
===================

The cookie name for ``access_token`` from JWT Authentication. Default is
``None``.

``JWT_AUTH_REFRESH_COOKIE``
===========================

The cookie name for ``refresh_token`` from JWT Authentication. Default is
``None``.

``JWT_AUTH_REFRESH_COOKIE_PATH``
================================

The cookie path for ``refresh_token`` from JWT Authentication. Default is
``'/'``.

``JWT_AUTH_SECURE``
===================

If set to ``True``, the cookie will only be sent through https scheme. Default
is ``False``.

``JWT_AUTH_HTTPONLY``
=====================

If set to ``True``, the client-side JavaScript will not be able to access the
cookie. Default is ``True``.

.. note:: ``refresh_token`` will not be sent if ``JWT_AUTH_HTTPONLY`` set to ``True``, set it to ``False`` if you need ``refresh_token``.

``JWT_AUTH_SAMESITE``
=====================

To tell the browser not to send this cookie when performing a cross-origin
request. Default is ``'Lax'``. SameSite isn't supported by all browsers.

``JWT_AUTH_RETURN_EXPIRATION``
==============================

If set to ``True``, the ``access_token`` and ``refresh_token`` expiration time
will be included in response on successful JWT Authentication in
``dj_rest_auth.views.LoginView``. Default is ``False``.

``JWT_AUTH_COOKIE_USE_CSRF``
============================

If set to ``True``, enable CSRF checks for only authenticated views when using
the JWT cookie for auth. Does not effect a client's ability to authenticate
using a JWT Bearer Auth header without a CSRF token. Default is ``False``.

``JWT_AUTH_COOKIE_ENFORCE_CSRF_ON_UNAUTHENTICATED``
===================================================

If set to ``True``, enables CSRF checks for authenticated and unauthenticated
views when using the JWT cookie for auth. It does not effect a client's ability
to authenticate using a JWT Bearer Auth header without a CSRF token (though
getting the JWT token in the first place without passing a CSRF token isnt
possible). Default is ``False``.
