import json

from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from dj_rest_auth.app_settings import api_settings
from dj_rest_auth.views import LoginView

from .models import WebAuthnCredential


class PasskeyRegisterBeginView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'dj_rest_auth'

    def get_serializer_class(self):
        return api_settings.PASSKEY_REGISTER_BEGIN_SERIALIZER

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        options_json = serializer.validated_data['options_json']
        return Response(json.loads(options_json), status=status.HTTP_200_OK)


class PasskeyRegisterCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'dj_rest_auth'

    def get_serializer_class(self):
        return api_settings.PASSKEY_REGISTER_COMPLETE_SERIALIZER

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        credential = serializer.validated_data['credential_obj']
        list_serializer = api_settings.PASSKEY_LIST_SERIALIZER(credential)
        return Response(list_serializer.data, status=status.HTTP_201_CREATED)


class PasskeyLoginBeginView(GenericAPIView):
    permission_classes = (AllowAny,)
    throttle_scope = 'dj_rest_auth'

    def get_serializer_class(self):
        return api_settings.PASSKEY_LOGIN_BEGIN_SERIALIZER

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        options_json = serializer.validated_data['options_json']
        session_id = serializer.validated_data['session_id']
        response_data = json.loads(options_json)
        response_data['session_id'] = session_id
        return Response(response_data, status=status.HTTP_200_OK)


class PasskeyLoginCompleteView(LoginView):

    def get_serializer_class(self):
        return api_settings.PASSKEY_LOGIN_COMPLETE_SERIALIZER

    def post(self, request, *args, **kwargs):
        self.request = request
        self.serializer = self.get_serializer(data=self.request.data)
        self.serializer.is_valid(raise_exception=True)
        self.login()
        return self.get_response()


class PasskeyListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'dj_rest_auth'

    def get_serializer_class(self):
        return api_settings.PASSKEY_LIST_SERIALIZER

    def get_queryset(self):
        return WebAuthnCredential.objects.filter(user=self.request.user).order_by('-created_at')


class PasskeyDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'dj_rest_auth'

    def get_queryset(self):
        return WebAuthnCredential.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return api_settings.PASSKEY_LIST_SERIALIZER
        return api_settings.PASSKEY_UPDATE_SERIALIZER
