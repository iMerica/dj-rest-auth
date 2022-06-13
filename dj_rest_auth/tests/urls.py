from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.twitter.views import TwitterOAuthAdapter
from django.urls import include, re_path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from rest_framework import permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import CharField
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenVerifyView

from dj_rest_auth.jwt_auth import get_refresh_view
from dj_rest_auth.registration.views import (
    SocialAccountDisconnectView, SocialAccountListView, SocialConnectView,
    SocialLoginView, RegisterView
)
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.social_serializers import (
    TwitterConnectSerializer, TwitterLoginSerializer,
)
from dj_rest_auth.urls import urlpatterns

from . import django_urls


class ExampleProtectedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, *args, **kwargs):
        return Response(dict(success=True))

    def post(self, *args, **kwargs):
        return Response(dict(success=True))


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class TwitterLogin(SocialLoginView):
    adapter_class = TwitterOAuthAdapter
    serializer_class = TwitterLoginSerializer


class FacebookConnect(SocialConnectView):
    adapter_class = FacebookOAuth2Adapter


class TwitterConnect(SocialConnectView):
    adapter_class = TwitterOAuthAdapter
    serializer_class = TwitterConnectSerializer


class TwitterLoginSerializerFoo(TwitterLoginSerializer):
    pass


class NoPassowrdRegisterSerializer(RegisterSerializer):
    password1 = CharField(write_only=True, default=None)
    password2 = CharField(write_only=True, default=None)

    def get_cleaned_data(self):
        return {
            "username": self.validated_data.get("username", ""),
            "email": self.validated_data.get("email", ""),
        }

    def validate_password1(self, password):
        if password:
            return super().validate_password1(password)
        return None

class NoPasswordRegisterView(RegisterView):
    serializer_class = NoPassowrdRegisterSerializer


@api_view(['POST'])
def twitter_login_view(request):
    serializer = TwitterLoginSerializerFoo(
        data={'access_token': '11223344', 'token_secret': '55667788'},
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)


class TwitterLoginNoAdapter(SocialLoginView):
    serializer_class = TwitterLoginSerializer


@ensure_csrf_cookie
@api_view(['GET'])
def get_csrf_cookie(request):
    return Response()


urlpatterns += [
    re_path(r'^rest-registration/', include('dj_rest_auth.registration.urls')),
    re_path(r'^rest-registration-no-password/', NoPasswordRegisterView.as_view(), name="no_password_rest_register"),
    re_path(r'^test-admin/', include(django_urls)),
    re_path(
        r'^account-email-verification-sent/$', TemplateView.as_view(),
        name='account_email_verification_sent',
    ),
    re_path(
        r'^account-confirm-email/(?P<key>[-:\w]+)/$', TemplateView.as_view(),
        name='account_confirm_email',
    ),
    re_path(r'^social-login/facebook/$', FacebookLogin.as_view(), name='fb_login'),
    re_path(r'^social-login/twitter/$', TwitterLogin.as_view(), name='tw_login'),
    re_path(r'^social-login/twitter-no-view/$', twitter_login_view, name='tw_login_no_view'),
    re_path(r'^social-login/twitter-no-adapter/$', TwitterLoginNoAdapter.as_view(), name='tw_login_no_adapter'),
    re_path(r'^social-login/facebook/connect/$', FacebookConnect.as_view(), name='fb_connect'),
    re_path(r'^social-login/twitter/connect/$', TwitterConnect.as_view(), name='tw_connect'),
    re_path(r'^socialaccounts/$', SocialAccountListView.as_view(), name='social_account_list'),
    re_path(r'^protected-view/$', ExampleProtectedView.as_view()),
    re_path(
        r'^socialaccounts/(?P<pk>\d+)/disconnect/$', SocialAccountDisconnectView.as_view(),
        name='social_account_disconnect',
    ),
    re_path(r'^accounts/', include('allauth.socialaccount.urls')),
    re_path(r'^getcsrf/', get_csrf_cookie, name='getcsrf'),
    re_path('^token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    re_path('^token/refresh/', get_refresh_view().as_view(), name='token_refresh'),
]
