from django.utils.functional import lazy
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress

def email_address_exists(email: str, exclude_user=None) -> str:
    """
    Slightly modified version of allauth.account.utils.email_address_exists
    """
    try:
        from allauth.account import app_settings as account_settings
    except ImportError:
        return ImportError(
            "allauth needs to be added to INSTALLED_APPS."
        )    

    emailaddresses = EmailAddress.objects
    if exclude_user:
        emailaddresses = emailaddresses.exclude(user=exclude_user)
    ret = emailaddresses.filter(email__iexact=email).exists()
    if not ret:
        email_field = account_settings.USER_MODEL_EMAIL_FIELD
        if email_field:
            users = get_user_model().objects
            if exclude_user:
                users = users.exclude(pk=exclude_user.pk)
            ret = users.filter(**{email_field + "__iexact": email}).exists()
    return ret


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
