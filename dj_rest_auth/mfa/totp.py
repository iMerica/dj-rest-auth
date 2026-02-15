import pyotp
from django.utils import timezone

from dj_rest_auth.app_settings import api_settings

from .models import Authenticator


def generate_totp_secret():
    return pyotp.random_base32()


def build_totp_uri(user, secret):
    issuer = api_settings.MFA_TOTP_ISSUER or None
    digits = api_settings.MFA_TOTP_DIGITS
    period = api_settings.MFA_TOTP_PERIOD
    totp = pyotp.TOTP(secret, digits=digits, interval=period)
    name = getattr(user, 'email', None) or str(user)
    return totp.provisioning_uri(name=name, issuer_name=issuer)


def validate_totp_code(secret, code):
    digits = api_settings.MFA_TOTP_DIGITS
    period = api_settings.MFA_TOTP_PERIOD
    totp = pyotp.TOTP(secret, digits=digits, interval=period)
    return totp.verify(str(code), valid_window=1)


class TOTP:
    @staticmethod
    def activate(user, secret):
        authenticator, _ = Authenticator.objects.update_or_create(
            user=user,
            type=Authenticator.Type.TOTP,
            defaults={'data': {'secret': secret}},
        )
        return authenticator

    @staticmethod
    def deactivate(user):
        Authenticator.objects.filter(
            user=user, type=Authenticator.Type.TOTP,
        ).delete()

    @staticmethod
    def get_secret(user):
        try:
            auth = Authenticator.objects.get(
                user=user, type=Authenticator.Type.TOTP,
            )
            return auth.data.get('secret')
        except Authenticator.DoesNotExist:
            return None

    @staticmethod
    def validate_code(user, code):
        secret = TOTP.get_secret(user)
        if not secret:
            return False
        if validate_totp_code(secret, code):
            Authenticator.objects.filter(
                user=user, type=Authenticator.Type.TOTP,
            ).update(last_used_at=timezone.now())
            return True
        return False
