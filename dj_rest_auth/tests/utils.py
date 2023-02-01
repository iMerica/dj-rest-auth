import contextlib

from dj_rest_auth.app_settings import api_settings


@contextlib.contextmanager
def override_api_settings(**settings):
    old_settings = {}
    not_exist = []
    for k, v in settings.items():
        # Save settings
        try:
            old_settings[k] = api_settings.user_settings[k]
        except KeyError:
            not_exist.append(k)

        # Install temporary settings
        api_settings.user_settings[k] = v

        # Delete any cached settings
        try:
            delattr(api_settings, k)
        except AttributeError:
            pass

    yield

    for k in settings.keys():
        # Delete temporary settings
        api_settings.user_settings.pop(k)

        # Restore saved settings
        try:
            api_settings.user_settings[k] = old_settings[k]
        except KeyError:
            if k in not_exist and k in api_settings.user_settings:
                api_settings.user_settings.pop(k)

        # Delete any cached settings
        try:
            delattr(api_settings, k)
        except AttributeError:
            pass