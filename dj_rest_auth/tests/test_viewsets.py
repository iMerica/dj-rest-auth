from django.test.utils import override_settings

from .test_api import APIBasicTests
from .test_social import TestSocialAuth, TestSocialConnectAuth

@override_settings(ROOT_URLCONF='tests.urls_viewsets')
class TestViewSetAPIBasicTests(APIBasicTests):
    USERNAME = 'person2'
    PASS = 'person'
    EMAIL = 'person2@world.com'
    NEW_PASS = 'new-test-pass'
    REGISTRATION_VIEW = 'rest_auth.runtests.RegistrationView'

    # data without user profile
    REGISTRATION_DATA = {
        'username': USERNAME,
        'password1': PASS,
        'password2': PASS,
    }

    REGISTRATION_DATA_WITH_EMAIL = REGISTRATION_DATA.copy()
    REGISTRATION_DATA_WITH_EMAIL['email'] = EMAIL

    BASIC_USER_DATA = {
        'first_name': 'John',
        'last_name': 'Smith',
        'email': EMAIL,
    }
    USER_DATA = BASIC_USER_DATA.copy()
    USER_DATA['newsletter_subscribe'] = True

@override_settings(ROOT_URLCONF='tests.urls_viewsets')
class TestViewSetSocialAuth(TestSocialAuth):
    pass

@override_settings(ROOT_URLCONF='tests.urls_viewsets')
class TestViewSetSocialConnectAuth(TestSocialConnectAuth):
    pass
