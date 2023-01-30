from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .app_settings import api_settings

def get_token_model():
    token_model = api_settings.TOKEN_MODEL
    session_login = api_settings.SESSION_LOGIN
    use_jwt = api_settings.USE_JWT
    
    if not any((session_login, token_model, use_jwt)):
        raise ImproperlyConfigured(
            'No authentication is configured for rest auth. You must enable one or '
            'more of `TOKEN_MODEL`, `USE_JWT` or `SESSION_LOGIN`'
        )
    return token_model

TokenModel = get_token_model()
