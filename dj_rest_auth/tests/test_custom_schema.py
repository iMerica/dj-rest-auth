from django.test import TestCase
from django.test import override_settings

from dj_rest_auth.views import LoginView
from rest_framework.schemas.openapi import SchemaGenerator
from rest_framework.schemas.openapi import AutoSchema


class SchemaTestCase(TestCase):
    def setUp(self):
        # AutoSchema supports a custom response serializer
        # as of 2021-04-20 (post 3.12.4 release)
        if not hasattr(AutoSchema, 'get_response_serializer'):
            self.skipTest('Only valid after rest_framework v3.12.4')
        super().setUp()


class TestLoginViewSchema(SchemaTestCase):
    @override_settings(REST_USE_JWT=True)
    def test_response_serializer_use_jwt(self):
        schema = SchemaGenerator().get_schema()
        responses = schema['paths']['/login/']['post']['responses']
        success_response = responses['201']['content']['application/json']
        self.assertEqual(success_response['schema']['$ref'], '#/components/schemas/JWT')

    @override_settings(REST_USE_JWT=True)
    def test_response_serializer_use_jwt_schema(self):
        schema = SchemaGenerator().get_schema()
        jwt = schema['components']['schemas']['JWT']
        user_properties = jwt['properties']['user']['properties']
        self.assertIn('email', user_properties)

    @override_settings(JWT_AUTH_RETURN_EXPIRATION=True)
    @override_settings(REST_USE_JWT=True)
    def test_response_serializer_use_jwt_expiration(self):
        schema = SchemaGenerator().get_schema()
        responses = schema['paths']['/login/']['post']['responses']
        success_response = responses['201']['content']['application/json']
        self.assertEqual(success_response['schema']['$ref'], '#/components/schemas/JWTWithExpiration')

    @override_settings(JWT_AUTH_RETURN_EXPIRATION=True)
    @override_settings(REST_USE_JWT=True)
    def test_response_serializer_use_jwt_expiration_schema(self):
        schema = SchemaGenerator().get_schema()
        jwt_schema = schema['components']['schemas']['JWTWithExpiration']
        self.assertIn('access_token_expiration', jwt_schema['properties'])
        self.assertIn('refresh_token_expiration', jwt_schema['properties'])

    def test_response_serializer_use_token(self):
        schema = SchemaGenerator().get_schema()
        responses = schema['paths']['/login/']['post']['responses']
        success_response = responses['201']['content']['application/json']
        self.assertEqual(success_response['schema']['$ref'], '#/components/schemas/Token')

    def test_response_serializer_use_token_schema(self):
        schema = SchemaGenerator().get_schema()
        props = schema['components']['schemas']['Token']['properties']
        self.assertIn('key', props)


class TestRegistrationViewSchema(SchemaTestCase):
    REGISTRATION_URLS = 'dj_rest_auth.registration.urls'

    def _get_schema(self):
        generator = SchemaGenerator(urlconf=self.REGISTRATION_URLS)
        return generator.get_schema()

    @override_settings(ACCOUNT_EMAIL_REQUIRED=True)
    @override_settings(ACCOUNT_EMAIL_VERIFICATION='mandatory')
    def test_email_verification_required(self):
        schema = self._get_schema()
        responses = schema['paths']['/']['post']['responses']
        success_response = responses['201']['content']['application/json']
        self.assertEqual(
            success_response['schema']['$ref'],
            '#/components/schemas/DetailResponse')

    @override_settings(ACCOUNT_EMAIL_REQUIRED=True)
    @override_settings(ACCOUNT_EMAIL_VERIFICATION='mandatory')
    def test_email_verification_required_schema(self):
        schema = self._get_schema()
        props = schema['components']['schemas']['DetailResponse']['properties']
        self.assertIn('detail', props)

    @override_settings(REST_USE_JWT=True)
    def test_use_jwt(self):
        schema = self._get_schema()
        responses = schema['paths']['/']['post']['responses']
        success_response = responses['201']['content']['application/json']
        self.assertEqual(
            success_response['schema']['$ref'],
            '#/components/schemas/JWT')
    
    @override_settings(REST_USE_JWT=True)
    def test_use_jwt_schema(self):
        schema = self._get_schema()
        props = schema['components']['schemas']['JWT']['properties']
        self.assertIn('access_token', props)

    def test_use_token(self):
        schema = self._get_schema()
        responses = schema['paths']['/']['post']['responses']
        success_response = responses['201']['content']['application/json']
        self.assertEqual(
            success_response['schema']['$ref'],
            '#/components/schemas/Token')
    
    def test_use_token_schema(self):
        schema = self._get_schema()
        props = schema['components']['schemas']['Token']['properties']
        self.assertIn('key', props)