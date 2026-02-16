from django.urls import re_path

from .views import (MFAStatusView, MFAVerifyView, RecoveryCodesRegenerateView,
                    RecoveryCodesView, TOTPActivateView, TOTPDeactivateView)

urlpatterns = [
    re_path(r'^mfa/verify/?$', MFAVerifyView.as_view(), name='mfa_verify'),
    re_path(r'^mfa/totp/activate/?$', TOTPActivateView.as_view(), name='mfa_totp_activate'),
    re_path(r'^mfa/totp/deactivate/?$', TOTPDeactivateView.as_view(), name='mfa_totp_deactivate'),
    re_path(r'^mfa/status/?$', MFAStatusView.as_view(), name='mfa_status'),
    re_path(r'^mfa/recovery-codes/?$', RecoveryCodesView.as_view(), name='mfa_recovery_codes'),
    re_path(
        r'^mfa/recovery-codes/regenerate/?$',
        RecoveryCodesRegenerateView.as_view(),
        name='mfa_recovery_codes_regenerate',
    ),
]
