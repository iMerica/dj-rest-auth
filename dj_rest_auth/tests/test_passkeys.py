import base64
from dataclasses import dataclass
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings

from dj_rest_auth.tests.mixins import APIClient, TestsMixin

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

User = get_user_model()

PASSKEY_SETTINGS = {
    'PASSKEY_RP_ID': 'localhost',
    'PASSKEY_RP_NAME': 'Test App',
    'PASSKEY_RP_ORIGINS': ['http://localhost:8000'],
}

FAKE_CREDENTIAL_ID = b'\x01\x02\x03\x04\x05\x06\x07\x08'
FAKE_PUBLIC_KEY = b'\x10\x20\x30\x40\x50\x60\x70\x80'
FAKE_CREDENTIAL_ID_B64 = base64.urlsafe_b64encode(FAKE_CREDENTIAL_ID).rstrip(b'=').decode()
FAKE_CHALLENGE = b'\xaa\xbb\xcc\xdd' * 8
FAKE_CHALLENGE_B64 = base64.b64encode(FAKE_CHALLENGE).decode()


@dataclass
class MockVerifiedRegistration:
    credential_id: bytes = FAKE_CREDENTIAL_ID
    credential_public_key: bytes = FAKE_PUBLIC_KEY
    sign_count: int = 0
    aaguid: str = '00000000-0000-0000-0000-000000000000'
    fmt: str = 'none'
    credential_type: str = 'public-key'
    user_verified: bool = True
    attestation_object: bytes = b''
    credential_device_type: str = 'single_device'
    credential_backed_up: bool = False


@dataclass
class MockVerifiedAuthentication:
    credential_id: bytes = FAKE_CREDENTIAL_ID
    new_sign_count: int = 1
    credential_device_type: str = 'single_device'
    credential_backed_up: bool = False
    user_verified: bool = True


def _make_fake_registration_options():
    from webauthn import generate_registration_options
    opts = generate_registration_options(
        rp_id='localhost',
        rp_name='Test App',
        user_name='testuser',
        user_id=b'1',
        challenge=FAKE_CHALLENGE,
    )
    return opts


def _make_fake_authentication_options():
    from webauthn import generate_authentication_options
    opts = generate_authentication_options(
        rp_id='localhost',
        challenge=FAKE_CHALLENGE,
    )
    return opts


FAKE_ATTESTATION_RESPONSE = {
    'id': FAKE_CREDENTIAL_ID_B64,
    'rawId': FAKE_CREDENTIAL_ID_B64,
    'type': 'public-key',
    'response': {
        'attestationObject': base64.urlsafe_b64encode(b'fake-attestation').rstrip(b'=').decode(),
        'clientDataJSON': base64.urlsafe_b64encode(b'fake-client-data').rstrip(b'=').decode(),
    },
    'transports': ['internal'],
}

FAKE_ASSERTION_RESPONSE = {
    'id': FAKE_CREDENTIAL_ID_B64,
    'rawId': FAKE_CREDENTIAL_ID_B64,
    'type': 'public-key',
    'response': {
        'authenticatorData': base64.urlsafe_b64encode(b'fake-auth-data').rstrip(b'=').decode(),
        'clientDataJSON': base64.urlsafe_b64encode(b'fake-client-data').rstrip(b'=').decode(),
        'signature': base64.urlsafe_b64encode(b'fake-signature').rstrip(b'=').decode(),
    },
}


@override_settings(ROOT_URLCONF='tests.urls')
class PasskeyRegistrationTests(TestsMixin, TestCase):
    USERNAME = 'testuser'
    PASS = 'testpassword123!'
    EMAIL = 'test@example.com'

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(self.USERNAME, self.EMAIL, self.PASS)
        self.register_begin_url = reverse('passkey_register_begin')
        self.register_complete_url = reverse('passkey_register_complete')
        self.login_url = reverse('rest_login')
        cache.clear()

    def _authenticate(self):
        self.post(self.login_url, data={'username': self.USERNAME, 'password': self.PASS}, status_code=200)
        self.token = self.response.json.get('key')

    @patch('dj_rest_auth.passkeys.serializers.generate_registration_options')
    def test_register_begin_returns_options(self, mock_gen):
        mock_gen.return_value = _make_fake_registration_options()
        self._authenticate()
        self.post(self.register_begin_url, data={'name': 'My Key'}, status_code=200)
        self.assertIn('challenge', self.response.json)
        self.assertIn('rp', self.response.json)
        self.assertIn('user', self.response.json)

    def test_register_begin_requires_auth(self):
        self.post(self.register_begin_url, data={})
        self.assertIn(self.response.status_code, (401, 403))

    @patch('dj_rest_auth.passkeys.serializers.verify_registration_response')
    @patch('dj_rest_auth.passkeys.serializers.generate_registration_options')
    def test_register_complete_creates_credential(self, mock_gen, mock_verify):
        mock_gen.return_value = _make_fake_registration_options()
        mock_verify.return_value = MockVerifiedRegistration()

        self._authenticate()
        self.post(self.register_begin_url, data={'name': 'My Key'}, status_code=200)

        self.post(
            self.register_complete_url,
            data={'credential': FAKE_ATTESTATION_RESPONSE, 'name': 'My Key'},
            status_code=201,
        )
        self.assertEqual(self.response.json['name'], 'My Key')
        self.assertIn('id', self.response.json)

        from dj_rest_auth.passkeys.models import WebAuthnCredential
        self.assertEqual(WebAuthnCredential.objects.filter(user=self.user).count(), 1)

    @patch('dj_rest_auth.passkeys.serializers.verify_registration_response')
    @patch('dj_rest_auth.passkeys.serializers.generate_registration_options')
    def test_register_complete_duplicate_rejected(self, mock_gen, mock_verify):
        mock_gen.return_value = _make_fake_registration_options()
        mock_verify.return_value = MockVerifiedRegistration()

        self._authenticate()

        # First registration
        self.post(self.register_begin_url, data={}, status_code=200)
        self.post(
            self.register_complete_url,
            data={'credential': FAKE_ATTESTATION_RESPONSE},
            status_code=201,
        )

        # Second registration with same credential
        self.post(self.register_begin_url, data={}, status_code=200)
        self.post(
            self.register_complete_url,
            data={'credential': FAKE_ATTESTATION_RESPONSE},
            status_code=400,
        )

    def test_register_complete_expired_challenge(self):
        self._authenticate()
        # No begin step, so no challenge in cache
        self.post(
            self.register_complete_url,
            data={'credential': FAKE_ATTESTATION_RESPONSE},
            status_code=400,
        )
        self.assertIn('expired', str(self.response.json).lower())


@override_settings(ROOT_URLCONF='tests.urls')
class PasskeyLoginTests(TestsMixin, TestCase):
    USERNAME = 'testuser'
    PASS = 'testpassword123!'
    EMAIL = 'test@example.com'

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(self.USERNAME, self.EMAIL, self.PASS)
        self.login_begin_url = reverse('passkey_login_begin')
        self.login_complete_url = reverse('passkey_login_complete')
        self.login_url = reverse('rest_login')
        cache.clear()

    def _create_credential(self):
        from dj_rest_auth.passkeys.models import WebAuthnCredential
        return WebAuthnCredential.objects.create(
            user=self.user,
            name='Test Key',
            credential_id=FAKE_CREDENTIAL_ID,
            public_key=FAKE_PUBLIC_KEY,
            sign_count=0,
            transports=['internal'],
            discoverable=True,
        )

    @patch('dj_rest_auth.passkeys.serializers.generate_authentication_options')
    def test_login_begin_returns_options(self, mock_gen):
        mock_gen.return_value = _make_fake_authentication_options()
        self.post(self.login_begin_url, data={}, status_code=200)
        self.assertIn('challenge', self.response.json)
        self.assertIn('session_id', self.response.json)

    @patch('dj_rest_auth.passkeys.serializers.generate_authentication_options')
    def test_login_begin_with_username(self, mock_gen):
        mock_gen.return_value = _make_fake_authentication_options()
        self._create_credential()
        self.post(self.login_begin_url, data={'username': self.USERNAME}, status_code=200)
        self.assertIn('challenge', self.response.json)

    @patch('dj_rest_auth.passkeys.serializers.verify_authentication_response')
    @patch('dj_rest_auth.passkeys.serializers.generate_authentication_options')
    def test_login_complete_returns_token(self, mock_gen, mock_verify):
        mock_gen.return_value = _make_fake_authentication_options()
        mock_verify.return_value = MockVerifiedAuthentication()

        self._create_credential()

        self.post(self.login_begin_url, data={}, status_code=200)
        session_id = self.response.json['session_id']

        self.post(
            self.login_complete_url,
            data={
                'credential': FAKE_ASSERTION_RESPONSE,
                'session_id': session_id,
            },
            status_code=200,
        )
        self.assertIn('key', self.response.json)

    @patch('dj_rest_auth.passkeys.serializers.verify_authentication_response')
    @patch('dj_rest_auth.passkeys.serializers.generate_authentication_options')
    def test_login_complete_updates_sign_count(self, mock_gen, mock_verify):
        mock_gen.return_value = _make_fake_authentication_options()
        mock_verify.return_value = MockVerifiedAuthentication(new_sign_count=5)

        cred = self._create_credential()

        self.post(self.login_begin_url, data={}, status_code=200)
        session_id = self.response.json['session_id']

        self.post(
            self.login_complete_url,
            data={
                'credential': FAKE_ASSERTION_RESPONSE,
                'session_id': session_id,
            },
            status_code=200,
        )

        cred.refresh_from_db()
        self.assertEqual(cred.sign_count, 5)
        self.assertIsNotNone(cred.last_used_at)

    @patch('dj_rest_auth.passkeys.serializers.verify_authentication_response')
    def test_login_complete_expired_challenge(self, mock_verify):
        self._create_credential()
        self.post(
            self.login_complete_url,
            data={
                'credential': FAKE_ASSERTION_RESPONSE,
                'session_id': 'nonexistent',
            },
            status_code=400,
        )

    @patch('dj_rest_auth.passkeys.serializers.verify_authentication_response')
    @patch('dj_rest_auth.passkeys.serializers.generate_authentication_options')
    def test_login_complete_invalid_assertion_rejected(self, mock_gen, mock_verify):
        mock_gen.return_value = _make_fake_authentication_options()
        mock_verify.side_effect = Exception('Invalid signature')

        self._create_credential()

        self.post(self.login_begin_url, data={}, status_code=200)
        session_id = self.response.json['session_id']

        self.post(
            self.login_complete_url,
            data={
                'credential': FAKE_ASSERTION_RESPONSE,
                'session_id': session_id,
            },
            status_code=400,
        )

    @patch('dj_rest_auth.passkeys.serializers.verify_authentication_response')
    @patch('dj_rest_auth.passkeys.serializers.generate_authentication_options')
    def test_login_complete_inactive_user_rejected(self, mock_gen, mock_verify):
        mock_gen.return_value = _make_fake_authentication_options()
        mock_verify.return_value = MockVerifiedAuthentication()

        self._create_credential()
        self.user.is_active = False
        self.user.save()

        self.post(self.login_begin_url, data={}, status_code=200)
        session_id = self.response.json['session_id']

        self.post(
            self.login_complete_url,
            data={
                'credential': FAKE_ASSERTION_RESPONSE,
                'session_id': session_id,
            },
            status_code=400,
        )


@override_settings(ROOT_URLCONF='tests.urls')
class PasskeyManagementTests(TestsMixin, TestCase):
    USERNAME = 'testuser'
    PASS = 'testpassword123!'
    EMAIL = 'test@example.com'

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(self.USERNAME, self.EMAIL, self.PASS)
        self.user2 = User.objects.create_user('otheruser', 'other@example.com', 'otherpass123!')
        self.list_url = reverse('passkey_list')
        self.login_url = reverse('rest_login')
        cache.clear()

    def _authenticate(self, username=None, password=None):
        username = username or self.USERNAME
        password = password or self.PASS
        self.post(self.login_url, data={'username': username, 'password': password}, status_code=200)
        self.token = self.response.json.get('key')

    def _create_credential(self, user=None, name='Test Key'):
        from dj_rest_auth.passkeys.models import WebAuthnCredential
        user = user or self.user
        return WebAuthnCredential.objects.create(
            user=user,
            name=name,
            credential_id=b'\x01\x02\x03\x04' + str(user.pk).encode() + name.encode(),
            public_key=FAKE_PUBLIC_KEY,
            sign_count=0,
            transports=['internal'],
            discoverable=True,
        )

    def test_list_requires_auth(self):
        self.get(self.list_url)
        self.assertIn(self.response.status_code, (401, 403))

    def test_list_shows_own_passkeys(self):
        self._authenticate()
        self._create_credential(name='Key 1')
        self._create_credential(name='Key 2')
        self._create_credential(user=self.user2, name='Other Key')

        self.get(self.list_url, status_code=200)
        self.assertEqual(len(self.response.json), 2)
        names = {p['name'] for p in self.response.json}
        self.assertEqual(names, {'Key 1', 'Key 2'})

    def test_rename_passkey(self):
        self._authenticate()
        cred = self._create_credential(name='Old Name')
        detail_url = reverse('passkey_detail', kwargs={'pk': cred.pk})

        self.patch(detail_url, data={'name': 'New Name'}, status_code=200)
        cred.refresh_from_db()
        self.assertEqual(cred.name, 'New Name')

    def test_delete_passkey(self):
        self._authenticate()
        cred = self._create_credential()
        detail_url = reverse('passkey_detail', kwargs={'pk': cred.pk})

        self.send_request('delete', detail_url, status_code=204)

        from dj_rest_auth.passkeys.models import WebAuthnCredential
        self.assertFalse(WebAuthnCredential.objects.filter(pk=cred.pk).exists())

    def test_cannot_access_other_users_passkey(self):
        self._authenticate()
        other_cred = self._create_credential(user=self.user2, name='Other Key')
        detail_url = reverse('passkey_detail', kwargs={'pk': other_cred.pk})

        self.get(detail_url, status_code=404)
        self.patch(detail_url, data={'name': 'Hacked'}, status_code=404)
        self.send_request('delete', detail_url, status_code=404)

    def test_retrieve_passkey(self):
        self._authenticate()
        cred = self._create_credential(name='My Key')
        detail_url = reverse('passkey_detail', kwargs={'pk': cred.pk})

        self.get(detail_url, status_code=200)
        self.assertEqual(self.response.json['name'], 'My Key')
        self.assertIn('credential_id', self.response.json)


@override_settings(ROOT_URLCONF='tests.urls')
class PasskeyLoginEdgeCaseTests(TestsMixin, TestCase):
    USERNAME = 'testuser'
    PASS = 'testpassword123!'
    EMAIL = 'test@example.com'

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(self.USERNAME, self.EMAIL, self.PASS)
        self.login_begin_url = reverse('passkey_login_begin')
        self.login_complete_url = reverse('passkey_login_complete')
        cache.clear()

    def _create_credential(self):
        from dj_rest_auth.passkeys.models import WebAuthnCredential
        return WebAuthnCredential.objects.create(
            user=self.user,
            name='Test Key',
            credential_id=FAKE_CREDENTIAL_ID,
            public_key=FAKE_PUBLIC_KEY,
            sign_count=0,
            transports=['internal'],
            discoverable=True,
        )

    @patch('dj_rest_auth.passkeys.serializers.generate_authentication_options')
    def test_login_begin_with_email(self, mock_gen):
        mock_gen.return_value = _make_fake_authentication_options()
        self._create_credential()
        self.post(self.login_begin_url, data={'email': self.EMAIL}, status_code=200)
        self.assertIn('challenge', self.response.json)
        self.assertIn('session_id', self.response.json)

    @patch('dj_rest_auth.passkeys.serializers.generate_authentication_options')
    def test_login_begin_nonexistent_user(self, mock_gen):
        mock_gen.return_value = _make_fake_authentication_options()
        self.post(self.login_begin_url, data={'username': 'noone'}, status_code=200)
        self.assertIn('challenge', self.response.json)
        self.assertIn('session_id', self.response.json)

    def test_login_complete_invalid_session_id_format(self):
        self.post(
            self.login_complete_url,
            data={
                'credential': FAKE_ASSERTION_RESPONSE,
                'session_id': 'not-a-valid-hex!!',
            },
            status_code=400,
        )

    def test_login_complete_invalid_session_id_too_short(self):
        self.post(
            self.login_complete_url,
            data={
                'credential': FAKE_ASSERTION_RESPONSE,
                'session_id': 'abcd',
            },
            status_code=400,
        )

    @patch('dj_rest_auth.passkeys.serializers.verify_authentication_response')
    @patch('dj_rest_auth.passkeys.serializers.generate_authentication_options')
    def test_login_complete_challenge_single_use(self, mock_gen, mock_verify):
        mock_gen.return_value = _make_fake_authentication_options()
        mock_verify.return_value = MockVerifiedAuthentication()

        self._create_credential()

        self.post(self.login_begin_url, data={}, status_code=200)
        session_id = self.response.json['session_id']

        # First use succeeds
        self.post(
            self.login_complete_url,
            data={'credential': FAKE_ASSERTION_RESPONSE, 'session_id': session_id},
            status_code=200,
        )

        # Replay with same session_id fails
        self.post(
            self.login_complete_url,
            data={'credential': FAKE_ASSERTION_RESPONSE, 'session_id': session_id},
            status_code=400,
        )
        self.assertIn('expired', str(self.response.json).lower())

    @patch('dj_rest_auth.passkeys.serializers.generate_authentication_options')
    def test_login_complete_credential_not_found(self, mock_gen):
        mock_gen.return_value = _make_fake_authentication_options()
        # No credential created — lookup will fail

        self.post(self.login_begin_url, data={}, status_code=200)
        session_id = self.response.json['session_id']

        self.post(
            self.login_complete_url,
            data={'credential': FAKE_ASSERTION_RESPONSE, 'session_id': session_id},
            status_code=400,
        )
        self.assertIn('not found', str(self.response.json).lower())

    @patch('dj_rest_auth.passkeys.serializers.generate_authentication_options')
    def test_login_complete_invalid_credential_format(self, mock_gen):
        mock_gen.return_value = _make_fake_authentication_options()

        self.post(self.login_begin_url, data={}, status_code=200)
        session_id = self.response.json['session_id']

        self.post(
            self.login_complete_url,
            data={'credential': 'not-a-dict', 'session_id': session_id},
            status_code=400,
        )
        self.assertIn('invalid', str(self.response.json).lower())


@override_settings(ROOT_URLCONF='tests.urls')
class PasskeyRegistrationEdgeCaseTests(TestsMixin, TestCase):
    USERNAME = 'testuser'
    PASS = 'testpassword123!'
    EMAIL = 'test@example.com'

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(self.USERNAME, self.EMAIL, self.PASS)
        self.register_begin_url = reverse('passkey_register_begin')
        self.register_complete_url = reverse('passkey_register_complete')
        self.login_url = reverse('rest_login')
        cache.clear()

    def _authenticate(self):
        self.post(self.login_url, data={'username': self.USERNAME, 'password': self.PASS}, status_code=200)
        self.token = self.response.json.get('key')

    @patch('dj_rest_auth.passkeys.serializers.verify_registration_response')
    @patch('dj_rest_auth.passkeys.serializers.generate_registration_options')
    def test_register_complete_default_name(self, mock_gen, mock_verify):
        mock_gen.return_value = _make_fake_registration_options()
        mock_verify.return_value = MockVerifiedRegistration()

        self._authenticate()
        self.post(self.register_begin_url, data={}, status_code=200)
        self.post(
            self.register_complete_url,
            data={'credential': FAKE_ATTESTATION_RESPONSE},
            status_code=201,
        )
        self.assertEqual(self.response.json['name'], 'Passkey')


@override_settings(ROOT_URLCONF='tests.urls')
class PasskeyConfigTests(TestsMixin, TestCase):
    USERNAME = 'testuser'
    PASS = 'testpassword123!'
    EMAIL = 'test@example.com'

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(self.USERNAME, self.EMAIL, self.PASS)
        self.register_begin_url = reverse('passkey_register_begin')
        self.login_url = reverse('rest_login')
        cache.clear()

    def _authenticate(self):
        self.post(self.login_url, data={'username': self.USERNAME, 'password': self.PASS}, status_code=200)
        self.token = self.response.json.get('key')

    def test_missing_rp_config_raises_error(self):
        from dj_rest_auth.tests.utils import override_api_settings
        self._authenticate()
        with override_api_settings(PASSKEY_RP_ID=None, PASSKEY_RP_NAME=None, PASSKEY_RP_ORIGINS=None):
            self.post(self.register_begin_url, data={}, status_code=400)


@override_settings(ROOT_URLCONF='tests.urls')
class PasskeyJWTLoginTests(TestsMixin, TestCase):
    USERNAME = 'testuser'
    PASS = 'testpassword123!'
    EMAIL = 'test@example.com'

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(self.USERNAME, self.EMAIL, self.PASS)
        self.login_begin_url = reverse('passkey_login_begin')
        self.login_complete_url = reverse('passkey_login_complete')
        cache.clear()

    def _create_credential(self):
        from dj_rest_auth.passkeys.models import WebAuthnCredential
        return WebAuthnCredential.objects.create(
            user=self.user,
            name='Test Key',
            credential_id=FAKE_CREDENTIAL_ID,
            public_key=FAKE_PUBLIC_KEY,
            sign_count=0,
            transports=['internal'],
            discoverable=True,
        )

    @patch('dj_rest_auth.passkeys.serializers.verify_authentication_response')
    @patch('dj_rest_auth.passkeys.serializers.generate_authentication_options')
    def test_login_complete_returns_jwt(self, mock_gen, mock_verify):
        from dj_rest_auth.tests.utils import override_api_settings
        mock_gen.return_value = _make_fake_authentication_options()
        mock_verify.return_value = MockVerifiedAuthentication()

        self._create_credential()

        with override_api_settings(USE_JWT=True):
            self.post(self.login_begin_url, data={}, status_code=200)
            session_id = self.response.json['session_id']

            self.post(
                self.login_complete_url,
                data={
                    'credential': FAKE_ASSERTION_RESPONSE,
                    'session_id': session_id,
                },
                status_code=200,
            )
            self.assertIn('access', self.response.json)
            self.assertIn('user', self.response.json)
