import hashlib
import hmac
import os

from django.utils import timezone

from dj_rest_auth.app_settings import api_settings

from .models import Authenticator


class RecoveryCodes:
    @staticmethod
    def _generate_codes(seed, count):
        codes = []
        for i in range(count):
            raw = hmac.new(
                bytes.fromhex(seed),
                msg=str(i).encode(),
                digestmod=hashlib.sha256,
            ).hexdigest()[:8]
            codes.append(f'{raw[:4]}-{raw[4:]}')
        return codes

    @staticmethod
    def activate(user):
        seed = os.urandom(32).hex()
        count = api_settings.MFA_RECOVERY_CODE_COUNT
        authenticator, _ = Authenticator.objects.update_or_create(
            user=user,
            type=Authenticator.Type.RECOVERY_CODES,
            defaults={'data': {'seed': seed, 'used_mask': 0}},
        )
        return RecoveryCodes._generate_codes(seed, count)

    @staticmethod
    def get_unused_codes(user):
        try:
            auth = Authenticator.objects.get(
                user=user, type=Authenticator.Type.RECOVERY_CODES,
            )
        except Authenticator.DoesNotExist:
            return []
        seed = auth.data['seed']
        used_mask = auth.data.get('used_mask', 0)
        count = api_settings.MFA_RECOVERY_CODE_COUNT
        all_codes = RecoveryCodes._generate_codes(seed, count)
        return [
            code for i, code in enumerate(all_codes)
            if not (used_mask & (1 << i))
        ]

    @staticmethod
    def validate_code(user, code):
        try:
            auth = Authenticator.objects.get(
                user=user, type=Authenticator.Type.RECOVERY_CODES,
            )
        except Authenticator.DoesNotExist:
            return False
        seed = auth.data['seed']
        used_mask = auth.data.get('used_mask', 0)
        count = api_settings.MFA_RECOVERY_CODE_COUNT
        all_codes = RecoveryCodes._generate_codes(seed, count)
        normalized = code.strip().lower()
        for i, c in enumerate(all_codes):
            if c == normalized and not (used_mask & (1 << i)):
                used_mask |= (1 << i)
                auth.data['used_mask'] = used_mask
                auth.save(update_fields=['data', 'last_used_at'])
                auth.last_used_at = timezone.now()
                auth.save(update_fields=['last_used_at'])
                return True
        return False

    @staticmethod
    def deactivate(user):
        Authenticator.objects.filter(
            user=user, type=Authenticator.Type.RECOVERY_CODES,
        ).delete()
