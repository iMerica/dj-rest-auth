from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, modify_settings, override_settings
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from dj_rest_auth.serializers import DynamicSerializerField
from dj_rest_auth.serializers import UserDetailsSerializer
from dj_rest_auth.serializers import DynamicFieldSerializerMetaclass
from dj_rest_auth.serializers import JWTSerializer


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


class TestDynamicSerializerField(TestCase):
    def test_setting_required(self):
        with self.assertRaises(KeyError):
            serializer = DynamicSerializerField()

    def test_setting_popped(self):
        serializer = DynamicSerializerField(setting='foo.bar')
        self.assertEqual(serializer.setting, 'foo.bar')

    def test_default_cls_popped(self):
        serializer = DynamicSerializerField(
            setting='foo.bar',
            default_cls='biz.baz')
        self.assertEqual(serializer.default_cls, 'biz.baz')


class DummyDynamicUserSerializer(
        serializers.Serializer, metaclass=DynamicFieldSerializerMetaclass):
    user = DynamicSerializerField(
        setting='DUMMY_SETTING.USER_DETAILS_SERIALIZER',
        default_cls='dj_rest_auth.serializers.UserDetailsSerializer')


class DummyAlternativeSettingsDynamicSerializer(
        serializers.Serializer, metaclass=DynamicFieldSerializerMetaclass):
    user = DynamicSerializerField(
        setting='DUMMY_SETTING.FOOBAR.USER_DETAILS_SERIALIZER',
        default_cls='dj_rest_auth.serializers.UserDetailsSerializer')


class DummyUserDetailsSerializer(UserDetailsSerializer):
    foobar = serializers.CharField()


class TestDynamicFieldSerializerMetaclass(TestCase):
    @override_settings(
        DUMMY_SETTING=
            {'USER_DETAILS_SERIALIZER': 'dj_rest_auth.tests.test_serializers.DummyDynamicUserSerializer'}
    )
    def test_setting_provided(self):
        serializer = DummyDynamicUserSerializer()
        import pdb; pdb.set_trace();
        self.assertIsInstance(
            serializer.fields['user'],
            DummyDynamicUserSerializer)

    def test_default_cls_fallback(self):
        serializer = DummyDynamicUserSerializer()
        self.assertIsInstance(
            serializer.fields['user'],
            UserDetailsSerializer)

    @override_settings(
        DUMMY_SETTING={
            'USER_DETAILS_SERIALIZER': {
                'FOOBAR': 'dj_rest_auth.tests.test_serializers.DummyDynamicUserSerializer'
            }
        }
    )
    def test_alternative_settings_setting_provided(self):
        serializer = DummyAlternativeSettingsDynamicSerializer()
        self.assertIsInstance(
            serializer.fields['user'],
            DummyDynamicUserSerializer)


class TestJWTSerializer(TestCase):
    @override_settings(
        REST_AUTH_SERIALIZER=
            {'USER_DETAILS_SERIALIZER': 'dj_rest_auth.tests.test_serializers.DummyDynamicUserSerializer'}
    )
    def test_setting_provided_serializer(self):
        serializer = JWTSerializer()
        self.assertIsInstance(
            serializer.fields['user'],
            DummyDynamicUserSerializer)

    def test_default_cls_serializer(self):
        serializer = JWTSerializer()
        self.assertIsInstance(
            serializer.fields['user'],
            UserDetailsSerializer)