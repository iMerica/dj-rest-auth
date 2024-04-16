
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookProvider
from allauth.socialaccount.models import SocialApp
from allauth.core.exceptions import ImmediateHttpResponse
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.test import TestCase, modify_settings, override_settings
from django.contrib.sites.models import Site
from django.http import HttpResponseBadRequest
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import MagicMock, patch

from dj_rest_auth.serializers import PasswordChangeSerializer, UserDetailsSerializer
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from dj_rest_auth.registration.views import SocialLoginView


User = get_user_model()


def validate_is_lower(username: str):
    if username.islower():
        return username
    raise ValidationError('username must be lower case')


custom_username_validators = [validate_is_lower]
validator_path = 'dj_rest_auth.tests.test_serializers.custom_username_validators'


class TestUserDetailsSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='alice', email='alice@test.com', first_name='Alice',
        )

    @override_settings(ACCOUNT_USERNAME_VALIDATORS=validator_path)
    def test_validate_username_with_all_auth_failure(self):
        serializer = UserDetailsSerializer(
            self.user, data={'username': 'TestUsername'}, partial=True,
        )
        self.assertEqual(False, serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                'username': [
                    ErrorDetail(string='username must be lower case', code='invalid'),
                ],
            },
        )

    @override_settings(ACCOUNT_USERNAME_VALIDATORS=validator_path)
    def test_validate_username_with_all_auth_success(self):
        serializer = UserDetailsSerializer(
            self.user, data={'username': 'test_username'}, partial=True,
        )
        self.assertEqual(True, serializer.is_valid())
        self.assertEqual(serializer.validated_data, {'username': 'test_username'})

    @modify_settings(INSTALLED_APPS={'remove': ['allauth', 'allauth.account']})
    @override_settings(ACCOUNT_USERNAME_VALIDATORS=validator_path)
    def test_validate_username_without_all_auth(self):
        serializer = UserDetailsSerializer(
            self.user, data={'username': 'TestUsername'}, partial=True,
        )
        self.assertEqual(True, serializer.is_valid())
        self.assertEqual(serializer.validated_data, {'username': 'TestUsername'})


class TestPasswordChangeSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(
            username='alice', email='alice@test.com', first_name='Alice',
        )
        request_data = {
            'new_password1': 'Password',
            'new_password2': 'Password'
        }
        request = APIRequestFactory().post(request_data, format='json')
        force_authenticate(request, user)

        cls.request_data = request_data
        cls.request = request

    def test_custom_validation(self):
        # Test custom validation success
        PasswordChangeSerializer.custom_validation = MagicMock(return_value=True)
        serializer = PasswordChangeSerializer(
            reverse("rest_password_change"),
            data=self.request_data
        )
        serializer.validate(self.request_data)
        PasswordChangeSerializer.custom_validation.assert_called_once_with(self.request_data)

        # Test custom validation error
        PasswordChangeSerializer.custom_validation = MagicMock(
            side_effect=ValidationError("failed")
        )
        serializer = PasswordChangeSerializer(
            reverse("rest_password_change"),
            data=self.request_data
        )
        with self.assertRaisesMessage(ValidationError, "failed"):
            serializer.validate(self.request_data)


class TestSocialLoginSerializer(TestCase):
    NO_VIEW_SUBMIT_ERROR = {"non_field_errors": ["View is not defined, pass it as a context variable"]}
    NO_ADAPTER_CLASS_PRESENT = {"non_field_errors": ["Define adapter_class in view"]}
    HTTP_BAD_REQUEST_MESSAGE = {"non_field_errors": ["Bad Request"]}
    INCORRECT_VALUE = {"non_field_errors": ["Incorrect value"]}

    @classmethod
    def setUpTestData(cls):
        cls.request_data = {"access_token": "token1234"}
        cls.request = APIRequestFactory().post(cls.request_data, format='json')
        social_app = SocialApp.objects.create(
            provider='facebook',
            name='Facebook',
            client_id='123123123',
            secret='321321321',
        )
        site = Site.objects.get_current()
        social_app.sites.add(site)

        cls.fb_response = {
            "id": "56527456",
            "first_name": "Alice",
            "last_name": "Test",
            "name": "Alcie Test",
            "name_format": "{first} {last}",
            "email": "alice@test.com"
        }

    def test_validate_no_view_submit(self):
        serializer = SocialLoginSerializer(data=self.request_data, context={'request': self.request})
        serializer.is_valid()
        self.assertDictEqual(serializer.errors, self.NO_VIEW_SUBMIT_ERROR)

    def test_validate_no_adpapter_class_present(self):
        dummy_view = SocialLoginView()
        serializer = SocialLoginSerializer(data=self.request_data, context={'request': self.request, 'view': dummy_view})
        serializer.is_valid()
        self.assertDictEqual(serializer.errors, self.NO_ADAPTER_CLASS_PRESENT)

    @patch('allauth.socialaccount.providers.facebook.views.fb_complete_login')
    @patch('allauth.socialaccount.adapter.DefaultSocialAccountAdapter.pre_social_login')
    def test_immediate_http_response_error(self, mock_pre_social_login, mock_fb_complete_login):
        dummy_view = SocialLoginView()
        dummy_view.adapter_class = FacebookOAuth2Adapter
        mock_pre_social_login.side_effect = lambda request, social_login: exec('raise ImmediateHttpResponse(HttpResponseBadRequest("Bad Request"))')
        mock_fb_complete_login.return_value = FacebookProvider(self.request, app=FacebookOAuth2Adapter).sociallogin_from_response(self.request, self.fb_response)
        serializer = SocialLoginSerializer(data=self.request_data, context={'request': self.request, 'view': dummy_view})
        serializer.is_valid()
        self.assertDictEqual(serializer.errors, self.HTTP_BAD_REQUEST_MESSAGE)

    def test_http_error(self):
        dummy_view = SocialLoginView()
        dummy_view.adapter_class = FacebookOAuth2Adapter
        serializer = SocialLoginSerializer(data=self.request_data, context={'request': self.request, 'view': dummy_view})
        serializer.is_valid()
        self.assertDictEqual(serializer.errors, self.INCORRECT_VALUE)
