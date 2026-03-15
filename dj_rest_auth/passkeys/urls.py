from django.urls import re_path

from .views import (
    PasskeyDetailView,
    PasskeyListView,
    PasskeyLoginBeginView,
    PasskeyLoginCompleteView,
    PasskeyRegisterBeginView,
    PasskeyRegisterCompleteView,
)

urlpatterns = [
    re_path(r'^register/begin/?$', PasskeyRegisterBeginView.as_view(), name='passkey_register_begin'),
    re_path(r'^register/complete/?$', PasskeyRegisterCompleteView.as_view(), name='passkey_register_complete'),
    re_path(r'^login/begin/?$', PasskeyLoginBeginView.as_view(), name='passkey_login_begin'),
    re_path(r'^login/complete/?$', PasskeyLoginCompleteView.as_view(), name='passkey_login_complete'),
    re_path(r'^/?$', PasskeyListView.as_view(), name='passkey_list'),
    re_path(r'^(?P<pk>[0-9]+)/?$', PasskeyDetailView.as_view(), name='passkey_detail'),
]
