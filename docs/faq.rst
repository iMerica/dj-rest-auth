FAQ
===

1. Why account_confirm_email url is defined but it is not usable?

    In /dj_rest_auth/registration/urls.py we can find something like this:

    .. code-block:: python

        url(r'^account-confirm-email/(?P<key>[-:\w]+)/$', TemplateView.as_view(),
            name='account_confirm_email'),

    This url is used by django-allauth. Empty TemplateView is defined just to allow reverse() call inside app - when email with verification link is being sent.

    You should override this view/url to handle it in your API client somehow and then, send post to /verify-email/ endpoint with proper key.
    If you don't want to use API on that step, then just use ConfirmEmailView view from:
    django-allauth https://github.com/pennersr/django-allauth/blob/master/allauth/account/views.py

2. How can I update UserProfile assigned to User model?

    Assuming you already have UserProfile model defined like this

    .. code-block:: python

        from django.db import models
        from django.contrib.auth.models import User

        class UserProfile(models.Model):
            user = models.OneToOneField(User, related_name='userprofile')
            # custom fields for user
            company_name = models.CharField(max_length=100)

    To allow update user details within one request send to dj_rest_auth.views.UserDetailsView view, create serializer like this:

    .. code-block:: python

        from rest_framework import serializers
        from dj_rest_auth.serializers import UserDetailsSerializer

        class UserProfileSerializer(serializers.ModelSerializer):
            class Meta:
                model = UserProfile
                fields = ('company_name',)

        class UserSerializer(UserDetailsSerializer):

            profile = UserProfileSerializer(source="userprofile")

            class Meta(UserDetailsSerializer.Meta):
                fields = UserDetailsSerializer.Meta.fields + ('profile',)

            def update(self, instance, validated_data):
                userprofile_serializer = self.fields['profile']
                userprofile_instance = instance.userprofile
                userprofile_data = validated_data.pop('userprofile', {})
                
                # to access the 'company_name' field in here
                # company_name = userprofile_data.get('company_name')
                
                # update the userprofile fields
                userprofile_serializer.update(userprofile_instance, userprofile_data) 
                
                instance = super().update(instance, validated_data)
                return instance

    And setup USER_DETAILS_SERIALIZER in django settings:

    .. code-block:: python

        REST_AUTH = {
            ...
            'USER_DETAILS_SERIALIZER': 'demo.serializers.UserSerializer',
        }
