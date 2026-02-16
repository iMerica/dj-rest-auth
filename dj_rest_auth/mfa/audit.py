import logging


logger = logging.getLogger('dj_rest_auth.mfa')


def log_mfa_event(event, *, user=None, request=None, level=logging.INFO, **details):
    user_id = getattr(user, 'pk', None)
    username = getattr(user, 'get_username', lambda: None)()

    ip_address = None
    user_agent = None
    if request is not None:
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

    payload = {
        'event': event,
        'user_id': user_id,
        'username': username,
        'ip_address': ip_address,
        'user_agent': user_agent,
    }
    payload.update(details)

    logger.log(level, 'MFA event: %s', event, extra={'mfa_event': payload})
