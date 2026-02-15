from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Authenticator(models.Model):
    class Type(models.TextChoices):
        TOTP = 'totp', _('TOTP')
        RECOVERY_CODES = 'recovery_codes', _('Recovery codes')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mfa_authenticators',
    )
    type = models.CharField(max_length=20, choices=Type.choices)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (('user', 'type'),)

    def __str__(self):
        return f'{self.user} - {self.get_type_display()}'
