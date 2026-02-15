import pyotp
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings, modify_settings

from dj_rest_auth.mfa.models import Authenticator
from dj_rest_auth.mfa.totp import TOTP, generate_totp_secret, validate_totp_code
from dj_rest_auth.mfa.recovery_codes import RecoveryCodes
from dj_rest_auth.mfa.utils import create_ephemeral_token, verify_ephemeral_token, is_mfa_enabled

from .mixins import TestsMixin, APIClient

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

User = get_user_model()


@override_settings(ROOT_URLCONF='dj_rest_auth.tests.mfa_urls')
@modify_settings(INSTALLED_APPS={'append': 'dj_rest_auth.mfa'})
class MFAUnitTests(TestCase):
    """Unit tests for MFA utilities, TOTP, and recovery codes."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123', email='test@example.com',
        )

    def test_generate_totp_secret(self):
        secret = generate_totp_secret()
        self.assertTrue(len(secret) > 0)

    def test_validate_totp_code(self):
        secret = generate_totp_secret()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        self.assertTrue(validate_totp_code(secret, code))
        self.assertFalse(validate_totp_code(secret, '000000'))

    def test_totp_activate_deactivate(self):
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)
        self.assertTrue(is_mfa_enabled(self.user))
        TOTP.deactivate(self.user)
        self.assertFalse(is_mfa_enabled(self.user))

    def test_totp_validate_code(self):
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)
        totp = pyotp.TOTP(secret)
        code = totp.now()
        self.assertTrue(TOTP.validate_code(self.user, code))
        self.assertFalse(TOTP.validate_code(self.user, '000000'))

    def test_totp_get_secret(self):
        self.assertIsNone(TOTP.get_secret(self.user))
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)
        self.assertEqual(TOTP.get_secret(self.user), secret)

    def test_recovery_codes_activate(self):
        codes = RecoveryCodes.activate(self.user)
        self.assertEqual(len(codes), 10)
        for code in codes:
            self.assertRegex(code, r'^[0-9a-f]{4}-[0-9a-f]{4}$')

    def test_recovery_codes_validate(self):
        codes = RecoveryCodes.activate(self.user)
        first_code = codes[0]
        self.assertTrue(RecoveryCodes.validate_code(self.user, first_code))
        # Same code should not work twice
        self.assertFalse(RecoveryCodes.validate_code(self.user, first_code))

    def test_recovery_codes_get_unused(self):
        codes = RecoveryCodes.activate(self.user)
        unused = RecoveryCodes.get_unused_codes(self.user)
        self.assertEqual(len(unused), 10)
        RecoveryCodes.validate_code(self.user, codes[0])
        unused = RecoveryCodes.get_unused_codes(self.user)
        self.assertEqual(len(unused), 9)

    def test_recovery_codes_deactivate(self):
        RecoveryCodes.activate(self.user)
        RecoveryCodes.deactivate(self.user)
        self.assertEqual(RecoveryCodes.get_unused_codes(self.user), [])

    def test_ephemeral_token(self):
        token = create_ephemeral_token(self.user)
        user = verify_ephemeral_token(token)
        self.assertEqual(user.pk, self.user.pk)

    def test_ephemeral_token_expired(self):
        from django.core.signing import SignatureExpired
        token = create_ephemeral_token(self.user)
        with self.assertRaises(SignatureExpired):
            verify_ephemeral_token(token, max_age=0)

    def test_is_mfa_enabled(self):
        self.assertFalse(is_mfa_enabled(self.user))
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)
        self.assertTrue(is_mfa_enabled(self.user))


@override_settings(ROOT_URLCONF='dj_rest_auth.tests.mfa_urls')
@modify_settings(INSTALLED_APPS={'append': 'dj_rest_auth.mfa'})
class MFALoginFlowTests(TestsMixin, TestCase):
    """Integration tests for MFA login flow."""

    USERNAME = 'testuser'
    PASS = 'testpass123'
    EMAIL = 'test@example.com'

    def setUp(self):
        self.init_mfa()

    def init_mfa(self):
        from django.conf import settings
        settings.DEBUG = True
        self.client = APIClient()
        self.user = User.objects.create_user(
            username=self.USERNAME, password=self.PASS, email=self.EMAIL,
        )
        self.login_url = reverse('rest_login')
        self.mfa_verify_url = reverse('mfa_verify')
        self.mfa_status_url = reverse('mfa_status')
        self.totp_activate_url = reverse('mfa_totp_activate')
        self.totp_deactivate_url = reverse('mfa_totp_deactivate')
        self.recovery_codes_url = reverse('mfa_recovery_codes')
        self.recovery_codes_regenerate_url = reverse('mfa_recovery_codes_regenerate')

    def _login_get_token(self):
        """Login without MFA and get auth token."""
        payload = {'username': self.USERNAME, 'password': self.PASS}
        response = self.post(self.login_url, data=payload, status_code=200)
        self.token = response.json.get('key')
        return response

    def _mfa_login_get_token(self, secret):
        """Login with MFA: get ephemeral token, verify with TOTP, return auth token."""
        payload = {'username': self.USERNAME, 'password': self.PASS}
        response = self.post(self.login_url, data=payload, status_code=200)
        ephemeral_token = response.json['ephemeral_token']
        totp = pyotp.TOTP(secret)
        code = totp.now()
        response = self.post(
            self.mfa_verify_url,
            data={'ephemeral_token': ephemeral_token, 'code': code},
            status_code=200,
        )
        self.token = response.json.get('key')
        return response

    def test_login_without_mfa(self):
        """Login without MFA should return normal token response."""
        payload = {'username': self.USERNAME, 'password': self.PASS}
        response = self.post(self.login_url, data=payload, status_code=200)
        self.assertIn('key', response.json)
        self.assertNotIn('ephemeral_token', response.json)

    def test_login_with_mfa_returns_ephemeral_token(self):
        """Login with MFA enabled should return ephemeral_token."""
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)

        payload = {'username': self.USERNAME, 'password': self.PASS}
        response = self.post(self.login_url, data=payload, status_code=200)
        self.assertIn('ephemeral_token', response.json)
        self.assertTrue(response.json['mfa_required'])
        self.assertNotIn('key', response.json)

    def test_mfa_verify_with_totp(self):
        """Verify MFA with valid TOTP code should return auth token."""
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)
        RecoveryCodes.activate(self.user)

        payload = {'username': self.USERNAME, 'password': self.PASS}
        response = self.post(self.login_url, data=payload, status_code=200)
        ephemeral_token = response.json['ephemeral_token']

        totp = pyotp.TOTP(secret)
        code = totp.now()
        response = self.post(
            self.mfa_verify_url,
            data={'ephemeral_token': ephemeral_token, 'code': code},
            status_code=200,
        )
        self.assertIn('key', response.json)

    def test_mfa_verify_with_recovery_code(self):
        """Verify MFA with a valid recovery code should return auth token."""
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)
        codes = RecoveryCodes.activate(self.user)

        payload = {'username': self.USERNAME, 'password': self.PASS}
        response = self.post(self.login_url, data=payload, status_code=200)
        ephemeral_token = response.json['ephemeral_token']

        response = self.post(
            self.mfa_verify_url,
            data={'ephemeral_token': ephemeral_token, 'code': codes[0]},
            status_code=200,
        )
        self.assertIn('key', response.json)

    def test_mfa_verify_invalid_code(self):
        """Verify MFA with invalid code should fail."""
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)

        payload = {'username': self.USERNAME, 'password': self.PASS}
        response = self.post(self.login_url, data=payload, status_code=200)
        ephemeral_token = response.json['ephemeral_token']

        response = self.post(
            self.mfa_verify_url,
            data={'ephemeral_token': ephemeral_token, 'code': '000000'},
            status_code=400,
        )

    def test_mfa_verify_invalid_token(self):
        """Verify MFA with invalid ephemeral token should fail."""
        response = self.post(
            self.mfa_verify_url,
            data={'ephemeral_token': 'invalid-token', 'code': '123456'},
            status_code=400,
        )

    def test_mfa_status_not_enabled(self):
        """MFA status should indicate not enabled."""
        self._login_get_token()
        response = self.get(self.mfa_status_url, status_code=200)
        self.assertFalse(response.json['mfa_enabled'])

    def test_mfa_status_enabled(self):
        """MFA status should indicate enabled after activation."""
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)
        # Must do full MFA login to get a token
        self._mfa_login_get_token(secret)
        response = self.get(self.mfa_status_url, status_code=200)
        self.assertTrue(response.json['mfa_enabled'])

    def test_totp_activate_get(self):
        """GET TOTP activate should return secret and totp_url."""
        self._login_get_token()
        response = self.get(self.totp_activate_url, status_code=200)
        self.assertIn('secret', response.json)
        self.assertIn('totp_url', response.json)

    def test_totp_activate_post(self):
        """POST TOTP activate should activate TOTP and return recovery codes."""
        self._login_get_token()
        response = self.get(self.totp_activate_url, status_code=200)
        secret = response.json['secret']

        totp = pyotp.TOTP(secret)
        code = totp.now()

        response = self.post(
            self.totp_activate_url,
            data={'secret': secret, 'code': code},
            status_code=200,
        )
        self.assertIn('recovery_codes', response.json)
        self.assertEqual(len(response.json['recovery_codes']), 10)
        self.assertTrue(is_mfa_enabled(self.user))

    def test_totp_deactivate(self):
        """Deactivating TOTP should remove MFA."""
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)
        self._mfa_login_get_token(secret)

        totp = pyotp.TOTP(secret)
        code = totp.now()
        response = self.post(
            self.totp_deactivate_url,
            data={'code': code},
            status_code=200,
        )
        self.assertFalse(is_mfa_enabled(self.user))

    def test_totp_deactivate_invalid_code(self):
        """Deactivating TOTP with invalid code should fail."""
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)
        self._mfa_login_get_token(secret)

        response = self.post(
            self.totp_deactivate_url,
            data={'code': '000000'},
            status_code=400,
        )
        self.assertTrue(is_mfa_enabled(self.user))

    def test_recovery_codes_view(self):
        """Should list unused recovery codes."""
        self._login_get_token()
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)
        RecoveryCodes.activate(self.user)

        response = self.get(self.recovery_codes_url, status_code=200)
        self.assertEqual(len(response.json['codes']), 10)

    def test_recovery_codes_regenerate(self):
        """Should regenerate new recovery codes."""
        secret = generate_totp_secret()
        TOTP.activate(self.user, secret)
        old_codes = RecoveryCodes.activate(self.user)
        self._mfa_login_get_token(secret)

        response = self.post(self.recovery_codes_regenerate_url, status_code=200)
        self.assertEqual(len(response.json['codes']), 10)
        self.assertNotEqual(response.json['codes'], old_codes)

    def test_recovery_codes_regenerate_without_mfa(self):
        """Should fail to regenerate when MFA is not enabled."""
        self._login_get_token()
        response = self.post(self.recovery_codes_regenerate_url, status_code=400)

    def test_full_mfa_flow(self):
        """End-to-end: activate MFA, login with TOTP, login with recovery code,
        regenerate recovery codes, deactivate MFA, login normally."""
        # 1. Login normally
        self._login_get_token()

        # 2. Check MFA status - not enabled
        response = self.get(self.mfa_status_url, status_code=200)
        self.assertFalse(response.json['mfa_enabled'])

        # 3. Get TOTP activation secret
        response = self.get(self.totp_activate_url, status_code=200)
        secret = response.json['secret']
        self.assertIn('totp_url', response.json)
        self.assertIn('qr_code_data_uri', response.json)

        # 4. Activate TOTP with valid code
        totp = pyotp.TOTP(secret)
        code = totp.now()
        response = self.post(
            self.totp_activate_url,
            data={'secret': secret, 'code': code},
            status_code=200,
        )
        recovery_codes = response.json['recovery_codes']
        self.assertEqual(len(recovery_codes), 10)

        # 5. Check MFA status - enabled
        response = self.get(self.mfa_status_url, status_code=200)
        self.assertTrue(response.json['mfa_enabled'])
        self.assertIsNotNone(response.json['created_at'])

        # 6. View recovery codes
        response = self.get(self.recovery_codes_url, status_code=200)
        self.assertEqual(len(response.json['codes']), 10)

        # 7. Clear token, login again - should get ephemeral token
        del self.token
        payload = {'username': self.USERNAME, 'password': self.PASS}
        response = self.post(self.login_url, data=payload, status_code=200)
        self.assertTrue(response.json['mfa_required'])
        self.assertNotIn('key', response.json)
        ephemeral_token = response.json['ephemeral_token']

        # 8. Verify with TOTP code
        code = totp.now()
        response = self.post(
            self.mfa_verify_url,
            data={'ephemeral_token': ephemeral_token, 'code': code},
            status_code=200,
        )
        self.assertIn('key', response.json)
        self.token = response.json['key']

        # 9. Check MFA status - last_used_at should now be set
        response = self.get(self.mfa_status_url, status_code=200)
        self.assertTrue(response.json['mfa_enabled'])
        self.assertIsNotNone(response.json['last_used_at'])

        # 10. Clear token, login again - this time use a recovery code
        del self.token
        payload = {'username': self.USERNAME, 'password': self.PASS}
        response = self.post(self.login_url, data=payload, status_code=200)
        ephemeral_token = response.json['ephemeral_token']

        response = self.post(
            self.mfa_verify_url,
            data={'ephemeral_token': ephemeral_token, 'code': recovery_codes[0]},
            status_code=200,
        )
        self.assertIn('key', response.json)
        self.token = response.json['key']

        # 11. Verify the used recovery code is consumed
        response = self.get(self.recovery_codes_url, status_code=200)
        self.assertEqual(len(response.json['codes']), 9)
        self.assertNotIn(recovery_codes[0], response.json['codes'])

        # 12. Regenerate recovery codes
        response = self.post(self.recovery_codes_regenerate_url, status_code=200)
        new_codes = response.json['codes']
        self.assertEqual(len(new_codes), 10)
        self.assertNotEqual(new_codes, recovery_codes)

        # 13. Verify old recovery codes no longer work
        del self.token
        payload = {'username': self.USERNAME, 'password': self.PASS}
        response = self.post(self.login_url, data=payload, status_code=200)
        ephemeral_token = response.json['ephemeral_token']

        response = self.post(
            self.mfa_verify_url,
            data={'ephemeral_token': ephemeral_token, 'code': recovery_codes[1]},
            status_code=400,
        )

        # 14. New recovery codes work
        response = self.post(
            self.mfa_verify_url,
            data={'ephemeral_token': ephemeral_token, 'code': new_codes[0]},
            status_code=200,
        )
        self.token = response.json['key']

        # 15. Invalid TOTP code is rejected
        del self.token
        payload = {'username': self.USERNAME, 'password': self.PASS}
        response = self.post(self.login_url, data=payload, status_code=200)
        ephemeral_token = response.json['ephemeral_token']

        response = self.post(
            self.mfa_verify_url,
            data={'ephemeral_token': ephemeral_token, 'code': '000000'},
            status_code=400,
        )

        # 16. Login with valid TOTP to get token for deactivation
        code = totp.now()
        response = self.post(
            self.mfa_verify_url,
            data={'ephemeral_token': ephemeral_token, 'code': code},
            status_code=200,
        )
        self.token = response.json['key']

        # 17. Deactivate TOTP (requires valid code)
        code = totp.now()
        response = self.post(
            self.totp_deactivate_url,
            data={'code': code},
            status_code=200,
        )

        # 18. Check MFA status - disabled
        response = self.get(self.mfa_status_url, status_code=200)
        self.assertFalse(response.json['mfa_enabled'])

        # 19. Login normally again - no MFA challenge
        del self.token
        payload = {'username': self.USERNAME, 'password': self.PASS}
        response = self.post(self.login_url, data=payload, status_code=200)
        self.assertIn('key', response.json)
        self.assertNotIn('ephemeral_token', response.json)
