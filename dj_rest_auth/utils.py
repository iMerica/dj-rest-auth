from importlib import import_module

from django.utils.functional import lazy


def import_callable(path_or_callable):
    if hasattr(path_or_callable, '__call__'):
        return path_or_callable
    else:
        assert isinstance(path_or_callable, str)
        package, attr = path_or_callable.rsplit('.', 1)
        return getattr(import_module(package), attr)


def default_create_token(token_model, user, serializer):
    token, _ = token_model.objects.get_or_create(user=user)
    return token


def jwt_encode(user):
    from dj_rest_auth.app_settings import api_settings

    JWTTokenClaimsSerializer = api_settings.JWT_TOKEN_CLAIMS_SERIALIZER

    refresh = JWTTokenClaimsSerializer.get_token(user)
    return refresh.access_token, refresh


def format_lazy(s, *args, **kwargs):
    return s.format(*args, **kwargs)


format_lazy = lazy(format_lazy, str)


try:
    from .jwt_auth import JWTCookieAuthentication
except ImportError:
    pass
