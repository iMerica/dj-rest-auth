from django.contrib.auth import get_user_model
from django.core import signing
from django.core.signing import TimestampSigner

from dj_rest_auth.app_settings import api_settings

from .models import Authenticator

UserModel = get_user_model()


def create_ephemeral_token(user):
    signer = TimestampSigner(salt='dj-rest-auth-mfa')
    return signer.sign(str(user.pk))


def verify_ephemeral_token(token, max_age=None):
    if max_age is None:
        max_age = api_settings.MFA_EPHEMERAL_TOKEN_TIMEOUT
    signer = TimestampSigner(salt='dj-rest-auth-mfa')
    user_pk = signer.unsign(token, max_age=max_age)
    return UserModel.objects.get(pk=user_pk)


def create_totp_activation_token(user, secret):
    payload = {'uid': user.pk, 'secret': secret}
    return signing.dumps(payload, salt='dj-rest-auth-mfa-activation')


def verify_totp_activation_token(token, max_age=None):
    if max_age is None:
        max_age = api_settings.MFA_EPHEMERAL_TOKEN_TIMEOUT
    payload = signing.loads(
        token,
        salt='dj-rest-auth-mfa-activation',
        max_age=max_age,
    )
    return payload


def is_mfa_enabled(user):
    return Authenticator.objects.filter(
        user=user, type=Authenticator.Type.TOTP,
    ).exists()
