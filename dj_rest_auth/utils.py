from django.utils.functional import lazy
from allauth.account.models import EmailAddress

def email_address_exists(email: str) -> bool:
    """Check if an email address exists in the EmailAddress table."""
    try:
        EmailAddress.objects.get(email=email)
    except EmailAddress.DoesNotExist:
        return False
    return True


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
