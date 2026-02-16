import io
import logging

from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from dj_rest_auth.app_settings import api_settings
from dj_rest_auth.views import LoginView

from .audit import log_mfa_event
from .models import Authenticator
from .recovery_codes import RecoveryCodes
from .totp import TOTP, build_totp_uri, generate_totp_secret
from .utils import (create_ephemeral_token, create_totp_activation_token,
                    is_mfa_enabled)


class MFALoginView(LoginView):
    """
    Subclass of LoginView that checks for MFA.

    If the user has MFA enabled, returns an ephemeral token instead of
    completing login. The client must then POST to mfa/verify/ to exchange
    the ephemeral token + TOTP code for a real auth token.
    """

    def login(self):
        self.user = self.serializer.validated_data['user']
        if is_mfa_enabled(self.user):
            self.ephemeral_token = create_ephemeral_token(self.user)
            return
        super().login()

    def get_response(self):
        if hasattr(self, 'ephemeral_token'):
            return Response(
                {
                    'ephemeral_token': self.ephemeral_token,
                    'mfa_required': True,
                },
                status=status.HTTP_200_OK,
            )
        return super().get_response()


@method_decorator(
    sensitive_post_parameters('code', 'ephemeral_token'),
    name='dispatch',
)
class MFAVerifyView(GenericAPIView):
    """Exchange ephemeral_token + TOTP/recovery code for a real auth token."""
    permission_classes = (AllowAny,)
    serializer_class = api_settings.MFA_VERIFY_SERIALIZER
    throttle_scope = 'dj_rest_auth'

    def get_serializer_class(self):
        return api_settings.MFA_VERIFY_SERIALIZER

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Set backend attribute for django.contrib.auth.login()
        if not hasattr(user, 'backend'):
            from django.conf import settings as django_settings
            backends = django_settings.AUTHENTICATION_BACKENDS
            user.backend = backends[0] if backends else 'django.contrib.auth.backends.ModelBackend'

        # Complete login using the same mechanism as LoginView
        login_view = LoginView()
        login_view.request = request
        login_view.format_kwarg = self.format_kwarg
        login_view.user = user

        from dj_rest_auth.models import get_token_model
        from dj_rest_auth.utils import jwt_encode

        token_model = get_token_model()
        if api_settings.USE_JWT:
            login_view.access_token, login_view.refresh_token = jwt_encode(user)
        elif token_model:
            login_view.token = api_settings.TOKEN_CREATOR(
                token_model, user, serializer,
            )

        if api_settings.SESSION_LOGIN:
            login_view.process_login()

        return login_view.get_response()


@method_decorator(
    sensitive_post_parameters('code'),
    name='dispatch',
)
class TOTPActivateView(GenericAPIView):
    """
    GET: Generate a new TOTP secret + provisioning URI + QR code.
    POST: Confirm TOTP activation with activation_token and a valid code.
    """
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'dj_rest_auth'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return api_settings.MFA_TOTP_ACTIVATE_INIT_SERIALIZER
        return api_settings.MFA_TOTP_ACTIVATE_CONFIRM_SERIALIZER

    def get(self, request, *args, **kwargs):
        secret = generate_totp_secret()
        totp_url = build_totp_uri(request.user, secret)
        qr_data_uri = self._generate_qr_data_uri(totp_url)
        activation_token = create_totp_activation_token(request.user, secret)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance={
            'secret': secret,
            'totp_url': totp_url,
            'qr_code_data_uri': qr_data_uri,
            'activation_token': activation_token,
        })
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if is_mfa_enabled(request.user):
            log_mfa_event(
                'activation_failed',
                user=request.user,
                request=request,
                level=logging.WARNING,
                reason='already_enabled',
            )
            return Response(
                {
                    'detail': _(
                        'MFA is already enabled. Deactivate it before activating again.',
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        secret = serializer.validated_data['secret']
        TOTP.activate(request.user, secret)
        codes = RecoveryCodes.activate(request.user)
        log_mfa_event(
            'activated',
            user=request.user,
            request=request,
            recovery_codes_count=len(codes),
        )

        return Response(
            {'recovery_codes': codes},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _generate_qr_data_uri(data):
        try:
            import qrcode
            import qrcode.image.svg
            img = qrcode.make(data, image_factory=qrcode.image.svg.SvgImage)
            buf = io.BytesIO()
            img.save(buf)
            import base64
            svg_b64 = base64.b64encode(buf.getvalue()).decode()
            return f'data:image/svg+xml;base64,{svg_b64}'
        except ImportError:
            return ''


@method_decorator(
    sensitive_post_parameters('code'),
    name='dispatch',
)
class TOTPDeactivateView(GenericAPIView):
    """Deactivate TOTP MFA. Requires a valid TOTP code to confirm."""
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'dj_rest_auth'

    def get_serializer_class(self):
        return api_settings.MFA_TOTP_DEACTIVATE_SERIALIZER

    def post(self, request, *args, **kwargs):
        if not is_mfa_enabled(request.user):
            log_mfa_event(
                'deactivation_failed',
                user=request.user,
                request=request,
                level=logging.WARNING,
                reason='not_enabled',
            )
            return Response(
                {'detail': _('MFA is not enabled.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        TOTP.deactivate(request.user)
        RecoveryCodes.deactivate(request.user)
        log_mfa_event(
            'deactivated',
            user=request.user,
            request=request,
        )

        return Response(
            {'detail': _('TOTP has been deactivated.')},
            status=status.HTTP_200_OK,
        )


class MFAStatusView(GenericAPIView):
    """Check whether the current user has MFA enabled."""
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'dj_rest_auth'

    def get_serializer_class(self):
        return api_settings.MFA_STATUS_SERIALIZER

    def get(self, request, *args, **kwargs):
        try:
            auth = Authenticator.objects.get(
                user=request.user, type=Authenticator.Type.TOTP,
            )
            data = {
                'mfa_enabled': True,
                'created_at': auth.created_at,
                'last_used_at': auth.last_used_at,
            }
        except Authenticator.DoesNotExist:
            data = {
                'mfa_enabled': False,
                'created_at': None,
                'last_used_at': None,
            }
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance=data)
        return Response(serializer.data)


class RecoveryCodesView(GenericAPIView):
    """View unused recovery codes."""
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'dj_rest_auth'

    def get_serializer_class(self):
        return api_settings.MFA_RECOVERY_CODES_SERIALIZER

    def get(self, request, *args, **kwargs):
        codes = RecoveryCodes.get_unused_codes(request.user)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance={'codes': codes})
        return Response(serializer.data)


class RecoveryCodesRegenerateView(GenericAPIView):
    """Regenerate recovery codes. Invalidates all previous codes."""
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'dj_rest_auth'

    def get_serializer_class(self):
        return api_settings.MFA_RECOVERY_CODES_SERIALIZER

    def post(self, request, *args, **kwargs):
        if not is_mfa_enabled(request.user):
            return Response(
                {'detail': _('MFA is not enabled.')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        codes = RecoveryCodes.activate(request.user)
        log_mfa_event(
            'recovery_codes_regenerated',
            user=request.user,
            request=request,
            recovery_codes_count=len(codes),
        )
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance={'codes': codes})
        return Response(serializer.data)
