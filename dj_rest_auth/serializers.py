from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import SetPasswordForm, PasswordResetForm
from django.urls import exceptions as url_exceptions
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers
from rest_framework.exceptions import ValidationError

from .app_settings import api_settings

if 'allauth' in settings.INSTALLED_APPS:
    from .forms import AllAuthPasswordResetForm

from .models import TokenModel

# Get the UserModel
UserModel = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def authenticate(self, **kwargs):
        return authenticate(self.context['request'], **kwargs)

    def _validate_email(self, email, password):
        if email and password:
            user = self.authenticate(email=email, password=password)
        else:
            msg = _('Must include "email" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username(self, username, password):
        if username and password:
            user = self.authenticate(username=username, password=password)
        else:
            msg = _('Must include "username" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username_email(self, username, email, password):
        if email and password:
            user = self.authenticate(email=email, password=password)
        elif username and password:
            user = self.authenticate(username=username, password=password)
        else:
            msg = _('Must include either "username" or "email" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def get_auth_user_using_allauth(self, username, email, password):
        from allauth.account import app_settings as allauth_account_settings

        login_methods = getattr(allauth_account_settings, "LOGIN_METHODS", None)

        # Authentication through email
        if login_methods is not None:
            is_email_only = login_methods == {allauth_account_settings.AuthenticationMethod.EMAIL}
        else:
            is_email_only = allauth_account_settings.AUTHENTICATION_METHOD == allauth_account_settings.AuthenticationMethod.EMAIL
        if is_email_only:
            return self._validate_email(email, password)

        # Authentication through username
        if login_methods is not None:
            is_username_only = login_methods == {allauth_account_settings.AuthenticationMethod.USERNAME}
        else:
            is_username_only = allauth_account_settings.AUTHENTICATION_METHOD == allauth_account_settings.AuthenticationMethod.USERNAME
        if is_username_only:
            return self._validate_username(username, password)

        # Authentication through either username or email
        return self._validate_username_email(username, email, password)

    def get_auth_user_using_orm(self, username, email, password):
        if email:
            try:
                username = UserModel.objects.get(email__iexact=email).get_username()
            except UserModel.DoesNotExist:
                pass

        if username:
            return self._validate_username_email(username, '', password)

        return None

    def get_auth_user(self, username, email, password):
        """
        Retrieve the auth user from given POST payload by using
        either `allauth` auth scheme or bare Django auth scheme.

        Returns the authenticated user instance if credentials are correct,
        else `None` will be returned
        """
        if 'allauth' in settings.INSTALLED_APPS:

            # When `is_active` of a user is set to False, allauth tries to return template html
            # which does not exist. This is the solution for it. See issue #264.
            try:
                return self.get_auth_user_using_allauth(username, email, password)
            except url_exceptions.NoReverseMatch:
                msg = _('Unable to log in with provided credentials.')
                raise exceptions.ValidationError(msg)
        return self.get_auth_user_using_orm(username, email, password)

    @staticmethod
    def validate_auth_user_status(user):
        if not user.is_active:
            msg = _('User account is disabled.')
            raise exceptions.ValidationError(msg)

    @staticmethod
    def validate_email_verification_status(user, email=None):
        from allauth.account import app_settings as allauth_account_settings
        if (
            allauth_account_settings.EMAIL_VERIFICATION == allauth_account_settings.EmailVerificationMethod.MANDATORY and not user.emailaddress_set.filter(email=user.email, verified=True).exists()
        ):
            raise serializers.ValidationError(_('E-mail is not verified.'))

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')
        user = self.get_auth_user(username, email, password)

        if not user:
            msg = _('Unable to log in with provided credentials.')
            raise exceptions.ValidationError(msg)

        # Did we get back an active user?
        self.validate_auth_user_status(user)

        # If required, is the email verified?
        if 'dj_rest_auth.registration' in settings.INSTALLED_APPS:
            self.validate_email_verification_status(user, email=email)

        attrs['user'] = user
        return attrs


class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer for Token model.
    """

    class Meta:
        model = TokenModel
        fields = ('key',)


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """

    @staticmethod
    def validate_username(username):
        if 'allauth.account' not in settings.INSTALLED_APPS:
            # We don't need to call the all-auth
            # username validator unless its installed
            return username

        from allauth.account.adapter import get_adapter
        username = get_adapter().clean_username(username)
        return username

    class Meta:
        extra_fields = []
        # see https://github.com/iMerica/dj-rest-auth/issues/181
        # UserModel.XYZ causing attribute error while importing other
        # classes from `serializers.py`. So, we need to check whether the auth model has
        # the attribute or not
        if hasattr(UserModel, 'USERNAME_FIELD'):
            extra_fields.append(UserModel.USERNAME_FIELD)
        if hasattr(UserModel, 'EMAIL_FIELD'):
            extra_fields.append(UserModel.EMAIL_FIELD)
        if hasattr(UserModel, 'first_name'):
            extra_fields.append('first_name')
        if hasattr(UserModel, 'last_name'):
            extra_fields.append('last_name')
        model = UserModel
        fields = ('pk', *extra_fields)
        read_only_fields = ('email',)


class JWTSerializer(serializers.Serializer):
    """
    Serializer for JWT authentication.
    """
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        """
        Required to allow using custom USER_DETAILS_SERIALIZER in
        JWTSerializer. Defining it here to avoid circular imports
        """
        JWTUserDetailsSerializer = api_settings.USER_DETAILS_SERIALIZER

        user_data = JWTUserDetailsSerializer(obj['user'], context=self.context).data
        return user_data


class JWTSerializerWithExpiration(JWTSerializer):
    """
    Serializer for JWT authentication with expiration times.
    """
    access_expiration = serializers.DateTimeField()
    refresh_expiration = serializers.DateTimeField()


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """
    email = serializers.EmailField()

    reset_form = None

    @property
    def password_reset_form_class(self):
        if 'allauth' in settings.INSTALLED_APPS:
            return AllAuthPasswordResetForm
        else:
            return PasswordResetForm

    def get_email_options(self):
        """Override this method to change default e-mail options"""
        return {}

    def validate_email(self, value):
        # Create PasswordResetForm with the serializer
        self.reset_form = self.password_reset_form_class(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(self.reset_form.errors)

        return value

    def save(self):
        if 'allauth' in settings.INSTALLED_APPS:
            from allauth.account.forms import default_token_generator
        else:
            from django.contrib.auth.tokens import default_token_generator

        request = self.context.get('request')
        # Set some values to trigger the send_email method.
        opts = {
            'use_https': request.is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),
            'request': request,
            'token_generator': default_token_generator,
        }

        opts.update(self.get_email_options())
        self.reset_form.save(**opts)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming a password reset attempt.
    """
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)
    uid = serializers.CharField()
    token = serializers.CharField()

    set_password_form_class = SetPasswordForm

    _errors = {}
    user = None
    set_password_form = None

    def custom_validation(self, attrs):
        pass

    def validate(self, attrs):
        if 'allauth' in settings.INSTALLED_APPS:
            from allauth.account.forms import default_token_generator
            from allauth.account.utils import url_str_to_user_pk as uid_decoder
        else:
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_decode as uid_decoder

        # Decode the uidb64 (allauth use base36) to uid to get User object
        try:
            uid = force_str(uid_decoder(attrs['uid']))
            self.user = UserModel._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            raise ValidationError({'uid': [_('Invalid value')]})

        if not default_token_generator.check_token(self.user, attrs['token']):
            raise ValidationError({'token': [_('Invalid value')]})

        self.custom_validation(attrs)
        # Construct SetPasswordForm instance
        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs,
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)

        return attrs

    def save(self):
        return self.set_password_form.save()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128)
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)

    set_password_form_class = SetPasswordForm

    set_password_form = None

    def __init__(self, *args, **kwargs):
        self.old_password_field_enabled = api_settings.OLD_PASSWORD_FIELD_ENABLED
        self.logout_on_password_change = api_settings.LOGOUT_ON_PASSWORD_CHANGE
        super().__init__(*args, **kwargs)

        if not self.old_password_field_enabled:
            self.fields.pop('old_password')

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    def validate_old_password(self, value):
        invalid_password_conditions = (
            self.old_password_field_enabled,
            self.user,
            not self.user.check_password(value),
        )

        if all(invalid_password_conditions):
            err_msg = _('Your old password was entered incorrectly. Please enter it again.')
            raise serializers.ValidationError(err_msg)
        return value

    def custom_validation(self, attrs):
        pass

    def validate(self, attrs):
        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs,
        )

        self.custom_validation(attrs)
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        return attrs

    def save(self):
        self.set_password_form.save()
        if not self.logout_on_password_change:
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(self.request, self.user)

        if api_settings.PASSWORD_CHANGE_REVOKE_TOKENS:
            self._revoke_other_tokens()

    def _revoke_other_tokens(self):
        """
        Revoke authentication tokens after password change.

        For DRF tokens: Revokes all tokens for the user. If THIS request was
        token-authenticated, issues a new token and stores it for the view to return.
        If THIS request was session-authenticated, revokes tokens but does not return one.

        For JWT tokens: Blacklists all refresh tokens. If THIS request was
        JWT-authenticated, issues fresh tokens for the current client.

        Results stored in instance variables for the view to handle:
        - self.new_token: New DRF token (only if request was token-authenticated)
        - self.new_access_token, self.new_refresh_token: New JWT tokens (only if JWT-authenticated)
        """
        import logging
        from django.conf import settings

        logger = logging.getLogger(__name__)
        self.new_token = None
        self.new_access_token = None
        self.new_refresh_token = None

        # Determine how THIS request was authenticated
        # Check successful_authenticator AND request.auth (which is set by the authenticator)
        from rest_framework.authentication import TokenAuthentication
        from .models import get_token_model

        authenticator = getattr(self.request, 'successful_authenticator', None)
        token_model = get_token_model()

        # Token auth: authenticator is TokenAuthentication OR request.auth is a token instance
        # (request.auth is the token object for token auth, None for session auth)
        is_token_auth = isinstance(authenticator, TokenAuthentication)
        if not is_token_auth and token_model:
            is_token_auth = isinstance(self.request.auth, token_model)

        # JWT check: authenticator is JWTAuthentication (covers JWTCookieAuthentication subclass)
        is_jwt_auth = False
        if api_settings.USE_JWT:
            try:
                from rest_framework_simplejwt.authentication import JWTAuthentication
                is_jwt_auth = isinstance(authenticator, JWTAuthentication)
            except ImportError:
                pass

        # Handle DRF auth tokens - revoke all tokens regardless of auth method
        try:
            from .models import get_token_model
            token_model = get_token_model()
            if token_model:
                deleted_count = token_model.objects.filter(user=self.user).delete()[0]
                if deleted_count > 0:
                    # Only issue new token if THIS request was token-authenticated
                    if is_token_auth:
                        self.new_token = token_model.objects.create(user=self.user)
                        logger.info(
                            f"Revoked {deleted_count} DRF token(s) and issued new token for user "
                            f"{self.user.pk} after password change"
                        )
                    else:
                        logger.info(
                            f"Revoked {deleted_count} DRF token(s) for user {self.user.pk} "
                            "after password change (no new token issued)"
                        )
        except Exception as e:
            logger.exception(
                f"Failed to revoke DRF tokens for user {self.user.pk} after password change: {e}"
            )

        # Handle JWT tokens - only if THIS request was JWT-authenticated
        if is_jwt_auth:
            try:
                # Blacklist all outstanding refresh tokens if blacklist app is installed
                if 'rest_framework_simplejwt.token_blacklist' in settings.INSTALLED_APPS:
                    from rest_framework_simplejwt.token_blacklist.models import (
                        OutstandingToken,
                        BlacklistedToken,
                    )

                    outstanding_tokens = OutstandingToken.objects.filter(user=self.user)

                    tokens_to_blacklist = [
                        BlacklistedToken(token=token)
                        for token in outstanding_tokens
                        if not hasattr(token, 'blacklistedtoken')
                    ]

                    if tokens_to_blacklist:
                        BlacklistedToken.objects.bulk_create(
                            tokens_to_blacklist,
                            ignore_conflicts=True
                        )
                        logger.info(
                            f"Blacklisted {len(tokens_to_blacklist)} JWT refresh token(s) for user "
                            f"{self.user.pk} after password change"
                        )
                else:
                    logger.warning(
                        f"JWT blacklist app not installed - old refresh tokens remain valid for user "
                        f"{self.user.pk}"
                    )

                # Issue fresh tokens to THIS client
                from .utils import jwt_encode
                self.new_access_token, self.new_refresh_token = jwt_encode(self.user)
                logger.info(
                    f"Issued fresh JWT tokens for user {self.user.pk} after password change"
                )

            except ImportError as e:
                logger.warning(
                    f"Failed to handle JWT tokens for user {self.user.pk}: {e}"
                )
            except Exception as e:
                logger.exception(
                    f"Failed to revoke/reissue JWT tokens for user {self.user.pk} after password change: {e}"
                )
