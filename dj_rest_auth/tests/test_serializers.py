from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.test import TestCase, modify_settings, override_settings
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import MagicMock

from dj_rest_auth.serializers import PasswordChangeSerializer, UserDetailsSerializer


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

