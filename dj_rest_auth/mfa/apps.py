from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MFAConfig(AppConfig):
    name = 'dj_rest_auth.mfa'
    label = 'dj_rest_auth_mfa'
    verbose_name = _('dj-rest-auth MFA')
    default_auto_field = 'django.db.models.BigAutoField'
