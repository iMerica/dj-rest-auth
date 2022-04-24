from django.conf import settings
from rest_framework.viewsets import ViewSetMixin
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated

from .views import LoginView, UserDetailsView, sensitive_post_parameters_m
from .app_settings import (
    JWTSerializer, JWTSerializerWithExpiration, LoginSerializer,
    PasswordChangeSerializer, PasswordResetConfirmSerializer,
    PasswordResetSerializer, TokenSerializer, UserDetailsSerializer,
    create_token
)

from .views import LoginViewMixin, LogoutViewMixin, PasswordResetMixin, PasswordChangeMixin, PasswordResetConfirmMixin

UNAUTHENTICATED_VIEWSET_METHODS = ('list', 'login', 'logout',
                                   'password_reset', 'password_reset_confirm')

class UserDetailsViewSet(ViewSetMixin, LoginViewMixin, LogoutViewMixin, PasswordResetMixin, PasswordChangeMixin,
                         PasswordResetConfirmMixin, UserDetailsView):
    serializer_classes = {
        'default': UserDetailsSerializer,
        'login': LoginSerializer,
        'password_change': PasswordChangeSerializer,
        'password_reset': PasswordResetSerializer,
        'password_reset_confirm': PasswordResetConfirmSerializer,
    }

    user = None
    access_token = None
    token = None

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_permissions(self):
        if self.action in UNAUTHENTICATED_VIEWSET_METHODS:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_classes['default'])

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @action(url_name='rest_login', detail=False, methods=('POST',))
    def login(self, request, *args, **kwargs):
        return super().login(request, *args, **kwargs)

    @action(url_name='rest_logout', detail=False, methods=('POST',))
    def logout(self, request, *args, **kwargs):
        return super().logout(request)

    @logout.mapping.get
    def get_logout(self, request, *args, **kwargs):
        if getattr(settings, 'ACCOUNT_LOGOUT_ON_GET', False):
            response = super().logout(request)
        else:
            response = self.http_method_not_allowed(request, *args, **kwargs)
        return self.finalize_response(request, response, *args, **kwargs)

    @action(url_name='rest_password_change', detail=False, methods=('POST',))
    def password_change(self, request, *args, **kwargs):
        return super().password_change(request, *args, **kwargs)

    @action(url_name='rest_password_reset', detail=False, methods=('POST',))
    def password_reset(self, request, *args, **kwargs):
        return super().password_reset(request, *args, **kwargs)

    @action(url_name='rest_password_reset_confirm', detail=False, methods=('POST',))
    def password_reset_confirm(self, request, *args, **kwargs):
        return super().password_reset_confirm(request, *args, **kwargs)
