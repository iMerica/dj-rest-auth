import logging

from django.core.signing import BadSignature, SignatureExpired
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .audit import log_mfa_event
from .recovery_codes import RecoveryCodes
from .totp import TOTP, validate_totp_code
from .utils import verify_ephemeral_token


class MFAVerifySerializer(serializers.Serializer):
    ephemeral_token = serializers.CharField(required=True)
    code = serializers.CharField(required=True)

    def validate(self, attrs):
        request = self.context.get('request')
        try:
            user = verify_ephemeral_token(attrs['ephemeral_token'])
        except (BadSignature, SignatureExpired):
            log_mfa_event(
                'verify_failed',
                request=request,
                level=logging.WARNING,
                reason='invalid_or_expired_token',
            )
            raise serializers.ValidationError(
                {'ephemeral_token': _('Invalid or expired token.')},
            )

        code = attrs['code']
        if TOTP.validate_code(user, code):
            attrs['user'] = user
            return attrs

        if RecoveryCodes.validate_code(user, code):
            log_mfa_event(
                'recovery_code_used',
                user=user,
                request=request,
            )
            attrs['user'] = user
            return attrs

        log_mfa_event(
            'verify_failed',
            user=user,
            request=request,
            level=logging.WARNING,
            reason='invalid_code',
        )
        raise serializers.ValidationError(
            {'code': _('Invalid code.')},
        )


class TOTPActivateInitSerializer(serializers.Serializer):
    secret = serializers.CharField(read_only=True)
    totp_url = serializers.CharField(read_only=True)
    qr_code_data_uri = serializers.CharField(read_only=True)


class TOTPActivateConfirmSerializer(serializers.Serializer):
    secret = serializers.CharField(required=True)
    code = serializers.CharField(required=True)

    def validate(self, attrs):
        if not validate_totp_code(attrs['secret'], attrs['code']):
            log_mfa_event(
                'activation_failed',
                user=self.context['request'].user,
                request=self.context.get('request'),
                level=logging.WARNING,
                reason='invalid_totp_code',
            )
            raise serializers.ValidationError(
                {'code': _('Invalid code. Please check your authenticator app and try again.')},
            )
        return attrs


class TOTPDeactivateSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)

    def validate_code(self, code):
        user = self.context['request'].user
        if not TOTP.validate_code(user, code):
            log_mfa_event(
                'deactivation_failed',
                user=user,
                request=self.context.get('request'),
                level=logging.WARNING,
                reason='invalid_totp_code',
            )
            raise serializers.ValidationError(
                _('Invalid code.'),
            )
        return code


class MFAStatusSerializer(serializers.Serializer):
    mfa_enabled = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True, allow_null=True)
    last_used_at = serializers.DateTimeField(read_only=True, allow_null=True)


class RecoveryCodesSerializer(serializers.Serializer):
    codes = serializers.ListField(child=serializers.CharField(), read_only=True)
