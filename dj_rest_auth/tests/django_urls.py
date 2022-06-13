# Moved in Django 1.8 from django to tests/auth_tests/urls.py

from django.urls import re_path
from django.contrib.auth.decorators import login_required
from django.contrib.auth.urls import urlpatterns


try:
    from django.contrib.auth.views import (
        login, logout, password_change, password_reset, password_reset_confirm,
    )
except ImportError:
    from django.contrib.auth.views import (
        LoginView, LogoutView, PasswordChangeView, PasswordResetConfirmView,
        PasswordResetView,
    )
    logout = LogoutView.as_view()
    login = LoginView.as_view()
    password_reset = PasswordResetView.as_view()
    password_change = PasswordChangeView.as_view()
    password_reset_confirm = PasswordResetConfirmView.as_view()


# special urls for auth test cases
urlpatterns += [
    re_path(r'^logout/custom_query/$', logout, dict(redirect_field_name='follow')),
    re_path(r'^logout/next_page/$', logout, dict(next_page='/somewhere/')),
    re_path(r'^logout/next_page/named/$', logout, dict(next_page='password_reset')),
    re_path(r'^password_reset_from_email/$', password_reset, dict(from_email='staffmember@example.com')),
    re_path(r'^password_reset/custom_redirect/$', password_reset, dict(post_reset_redirect='/custom/')),
    re_path(r'^password_reset/custom_redirect/named/$', password_reset, dict(post_reset_redirect='password_reset')),
    re_path(
        r'^password_reset/html_email_template/$', password_reset,
        dict(html_email_template_name='registration/html_password_reset_email.html'),
    ),
    re_path(
        r'^reset/custom/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        password_reset_confirm,
        dict(post_reset_redirect='/custom/'),
    ),
    re_path(
        r'^reset/custom/named/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        password_reset_confirm,
        dict(post_reset_redirect='password_reset'),
    ),
    re_path(r'^password_change/custom/$', password_change, dict(post_change_redirect='/custom/')),
    re_path(r'^password_change/custom/named/$', password_change, dict(post_change_redirect='password_reset')),
    re_path(r'^admin_password_reset/$', password_reset, dict(is_admin_site=True)),
    re_path(r'^login_required/$', login_required(password_reset)),
    re_path(r'^login_required_login_url/$', login_required(password_reset, login_url='/somewhere/')),
]
