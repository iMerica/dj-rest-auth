from rest_framework.permissions import AllowAny

from ..app_settings import api_settings


RegisterSerializer = api_settings.REGISTER_SERIALIZER


def register_permission_classes():
    permission_classes = [AllowAny]
    permission_classes.extend(api_settings.REGISTER_PERMISSION_CLASSES)
    return tuple(permission_classes)
