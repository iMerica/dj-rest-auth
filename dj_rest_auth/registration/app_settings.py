from django.conf import settings
from rest_framework.permissions import AllowAny

from ..app_settings import api_settings

from ..utils import import_callable


RegisterSerializer = api_settings.REGISTER_SERIALIZER


def register_permission_classes():
    permission_classes = [AllowAny]
    for klass in api_settings.REST_AUTH_REGISTER_PERMISSION_CLASSES:
        permission_classes.append(import_callable(klass))
    return tuple(permission_classes)
