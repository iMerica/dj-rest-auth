import base64
import uuid

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import options_to_json
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
)

from dj_rest_auth.app_settings import api_settings

from .models import WebAuthnCredential

UserModel = get_user_model()


def _get_rp_settings():
    rp_id = api_settings.PASSKEY_RP_ID
    rp_name = api_settings.PASSKEY_RP_NAME
    rp_origins = api_settings.PASSKEY_RP_ORIGINS
    if not rp_id or not rp_name or not rp_origins:
        raise exceptions.ValidationError(
            _('Passkey RP settings (PASSKEY_RP_ID, PASSKEY_RP_NAME, PASSKEY_RP_ORIGINS) must be configured.')
        )
    return rp_id, rp_name, rp_origins


class PasskeyRegisterBeginSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, default='')

    def validate(self, attrs):
        user = self.context['request'].user
        rp_id, rp_name, rp_origins = _get_rp_settings()

        existing_credentials = WebAuthnCredential.objects.filter(user=user)
        exclude_credentials = [
            PublicKeyCredentialDescriptor(id=cred.credential_id)
            for cred in existing_credentials
        ]

        options = generate_registration_options(
            rp_id=rp_id,
            rp_name=rp_name,
            user_name=user.get_username(),
            user_id=str(user.pk).encode(),
            user_display_name=user.get_full_name() or user.get_username(),
            exclude_credentials=exclude_credentials,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
            ),
            timeout=api_settings.PASSKEY_CHALLENGE_TIMEOUT * 1000,
        )

        cache_key = f'webauthn_reg_{user.pk}'
        cache.set(cache_key, base64.b64encode(options.challenge).decode(), api_settings.PASSKEY_CHALLENGE_TIMEOUT)

        attrs['options_json'] = options_to_json(options)
        attrs['name'] = attrs.get('name', '')
        return attrs


class PasskeyRegisterCompleteSerializer(serializers.Serializer):
    credential = serializers.JSONField()
    name = serializers.CharField(required=False, default='')

    def validate(self, attrs):
        user = self.context['request'].user
        rp_id, rp_name, rp_origins = _get_rp_settings()

        cache_key = f'webauthn_reg_{user.pk}'
        challenge_b64 = cache.get(cache_key)
        if not challenge_b64:
            raise exceptions.ValidationError(_('Registration challenge has expired. Please start over.'))

        challenge = base64.b64decode(challenge_b64)
        cache.delete(cache_key)

        try:
            verification = verify_registration_response(
                credential=attrs['credential'],
                expected_challenge=challenge,
                expected_rp_id=rp_id,
                expected_origin=rp_origins,
            )
        except Exception:
            raise exceptions.ValidationError(_('Registration verification failed.'))

        if WebAuthnCredential.objects.filter(credential_id=verification.credential_id).exists():
            raise exceptions.ValidationError(_('This credential is already registered.'))

        transports = []
        cred_data = attrs['credential']
        if isinstance(cred_data, dict) and 'response' in cred_data:
            transports = cred_data.get('transports', [])

        name = attrs.get('name', '') or _('Passkey')
        credential = WebAuthnCredential.objects.create(
            user=user,
            name=name,
            credential_id=verification.credential_id,
            public_key=verification.credential_public_key,
            sign_count=verification.sign_count,
            transports=transports,
            discoverable=True,
        )

        attrs['credential_obj'] = credential
        return attrs


class PasskeyLoginBeginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        rp_id, rp_name, rp_origins = _get_rp_settings()

        allow_credentials = None
        username = attrs.get('username', '').strip()
        email = attrs.get('email', '').strip()

        if username or email:
            lookup = {}
            if username:
                lookup[UserModel.USERNAME_FIELD] = username
            elif email:
                lookup[UserModel.EMAIL_FIELD] = email
            try:
                user = UserModel.objects.get(**lookup)
                credentials = WebAuthnCredential.objects.filter(user=user)
                allow_credentials = [
                    PublicKeyCredentialDescriptor(
                        id=cred.credential_id,
                    )
                    for cred in credentials
                ]
            except UserModel.DoesNotExist:
                pass  # Intentional: fall through to discoverable credentials flow

        options = generate_authentication_options(
            rp_id=rp_id,
            allow_credentials=allow_credentials,
            timeout=api_settings.PASSKEY_CHALLENGE_TIMEOUT * 1000,
        )

        session_id = uuid.uuid4().hex
        cache_key = f'webauthn_auth_{session_id}'
        cache.set(cache_key, base64.b64encode(options.challenge).decode(), api_settings.PASSKEY_CHALLENGE_TIMEOUT)

        attrs['options_json'] = options_to_json(options)
        attrs['session_id'] = session_id
        return attrs


class PasskeyLoginCompleteSerializer(serializers.Serializer):
    credential = serializers.JSONField()
    session_id = serializers.RegexField(r'^[0-9a-f]{32}$')

    def validate(self, attrs):
        rp_id, rp_name, rp_origins = _get_rp_settings()

        cache_key = f'webauthn_auth_{attrs["session_id"]}'
        challenge_b64 = cache.get(cache_key)
        if not challenge_b64:
            raise exceptions.ValidationError(_('Authentication challenge has expired. Please start over.'))

        challenge = base64.b64decode(challenge_b64)
        cache.delete(cache_key)

        cred_data = attrs['credential']
        if isinstance(cred_data, dict):
            raw_id = cred_data.get('rawId', cred_data.get('id', ''))
        else:
            raise exceptions.ValidationError(_('Invalid credential format.'))

        credential_id_bytes = base64.urlsafe_b64decode(raw_id + '==')

        try:
            stored_credential = WebAuthnCredential.objects.get(credential_id=credential_id_bytes)
        except WebAuthnCredential.DoesNotExist:
            raise exceptions.ValidationError(_('Credential not found.'))

        try:
            verification = verify_authentication_response(
                credential=cred_data,
                expected_challenge=challenge,
                expected_rp_id=rp_id,
                expected_origin=rp_origins,
                credential_public_key=bytes(stored_credential.public_key),
                credential_current_sign_count=stored_credential.sign_count,
            )
        except Exception:
            raise exceptions.ValidationError(_('Authentication verification failed.'))

        stored_credential.sign_count = verification.new_sign_count
        stored_credential.last_used_at = timezone.now()
        stored_credential.save(update_fields=['sign_count', 'last_used_at'])

        user = stored_credential.user
        if not user.is_active:
            raise exceptions.ValidationError(_('User account is disabled.'))

        from django.conf import settings as django_settings
        backends = django_settings.AUTHENTICATION_BACKENDS
        user.backend = backends[0] if backends else 'django.contrib.auth.backends.ModelBackend'
        attrs['user'] = user
        return attrs


class PasskeyListSerializer(serializers.ModelSerializer):
    credential_id = serializers.SerializerMethodField()

    class Meta:
        model = WebAuthnCredential
        fields = ('id', 'name', 'credential_id', 'created_at', 'last_used_at', 'transports', 'discoverable')
        read_only_fields = ('id', 'credential_id', 'created_at', 'last_used_at', 'transports', 'discoverable')

    def get_credential_id(self, obj):
        return base64.urlsafe_b64encode(bytes(obj.credential_id)).rstrip(b'=').decode('ascii')


class PasskeyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebAuthnCredential
        fields = ('name',)
