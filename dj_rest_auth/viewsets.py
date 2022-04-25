from django.conf import settings
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.serializers import Serializer
from django.contrib.auth import get_user_model

from .app_settings import (
    JWTSerializer, JWTSerializerWithExpiration, LoginSerializer,
    PasswordChangeSerializer, PasswordResetConfirmSerializer,
    PasswordResetSerializer, TokenSerializer, UserDetailsSerializer,
    create_token
)
from .views import (
    LoginViewMixin, LogoutViewMixin, PasswordResetMixin, PasswordChangeMixin,
    PasswordResetConfirmMixin, sensitive_post_parameters_m
)


class UserDetailsViewSet(LoginViewMixin, LogoutViewMixin, PasswordResetMixin,
                         PasswordChangeMixin, PasswordResetConfirmMixin,
                         RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_classes = {
        'default': UserDetailsSerializer,
        'login': LoginSerializer,
        'password_change': PasswordChangeSerializer,
        'password_reset': PasswordResetSerializer,
        'password_reset_confirm': PasswordResetConfirmSerializer,
        'logout': Serializer
    }

    user = None
    access_token = None
    token = None

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        """
        Adding this method since it is sometimes called when using
        django-rest-swagger
        """
        return get_user_model().objects.none()

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_permissions(self):
        permission_classes = [AllowAny]
        for method in ('password_change', 'list'):
            if method in self.action_map.values():
                permission_classes = [IsAuthenticatedOrReadOnly]
                break
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
