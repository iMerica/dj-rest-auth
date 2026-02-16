# Customization

dj-rest-auth is designed to be highly customizable. Every serializer can be overridden, and there are hooks for custom validation logic.

## Overriding Serializers

All serializers can be replaced by setting the corresponding `REST_AUTH` setting to your custom serializer's dotted path.

### Custom Login Serializer

Add extra validation or modify login behavior:

```python title="serializers.py"
from dj_rest_auth.serializers import LoginSerializer
from rest_framework import serializers

class CustomLoginSerializer(LoginSerializer):
    organization = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        
        # Custom validation: check organization membership
        organization = attrs.get('organization')
        if organization:
            user = attrs['user']
            if not user.organizations.filter(slug=organization).exists():
                raise serializers.ValidationError(
                    {'organization': 'You are not a member of this organization.'}
                )
        
        return attrs
```

```python title="settings.py"
REST_AUTH = {
    'LOGIN_SERIALIZER': 'myapp.serializers.CustomLoginSerializer',
}
```

---

### Custom User Details Serializer

Customize which fields are returned and editable:

```python title="serializers.py"
from dj_rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers

class CustomUserDetailsSerializer(UserDetailsSerializer):
    # Add a nested profile
    profile = ProfileSerializer(source='userprofile', required=False)
    
    # Add computed fields
    full_name = serializers.SerializerMethodField()
    
    class Meta(UserDetailsSerializer.Meta):
        fields = (
            'pk', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'profile'
        )
        read_only_fields = ('pk', 'email', 'full_name')

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def update(self, instance, validated_data):
        # Handle nested profile update
        profile_data = validated_data.pop('userprofile', {})
        instance = super().update(instance, validated_data)
        
        if profile_data:
            profile = instance.userprofile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance
```

```python title="settings.py"
REST_AUTH = {
    'USER_DETAILS_SERIALIZER': 'myapp.serializers.CustomUserDetailsSerializer',
}
```

---

### Custom Registration Serializer

Add extra fields to registration:

```python title="serializers.py"
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from allauth.account.adapter import get_adapter

class CustomRegisterSerializer(RegisterSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    company = serializers.CharField(required=False, allow_blank=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data.update({
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
            'phone_number': self.validated_data.get('phone_number', ''),
            'company': self.validated_data.get('company', ''),
        })
        return data

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        
        user = adapter.save_user(request, user, self, commit=False)
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.save()
        
        # Create profile with extra fields
        user.profile.phone_number = self.cleaned_data.get('phone_number')
        user.profile.company = self.cleaned_data.get('company')
        user.profile.save()
        
        self.custom_signup(request, user)
        return user
```

!!! warning "Required Method"
    Your custom `RegisterSerializer` **must** define a `save(self, request)` method that returns a user instance.

---

### Custom JWT Claims

Add custom claims to your JWT tokens:

```python title="serializers.py"
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenClaimsSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        token['permissions'] = list(user.get_all_permissions())
        
        # Add profile data
        if hasattr(user, 'profile'):
            token['organization_id'] = user.profile.organization_id
        
        return token
```

```python title="settings.py"
REST_AUTH = {
    'USE_JWT': True,
    'JWT_TOKEN_CLAIMS_SERIALIZER': 'myapp.serializers.CustomTokenClaimsSerializer',
}
```

---

## Custom Token Creator

Control how tokens are created on login:

```python title="utils.py"
def custom_create_token(token_model, user, serializer):
    """
    Create a new token on every login (invalidating previous tokens).
    """
    # Delete existing tokens for this user
    token_model.objects.filter(user=user).delete()
    
    # Create new token
    token = token_model.objects.create(user=user)
    
    # Optional: Log the login
    from myapp.models import LoginHistory
    LoginHistory.objects.create(
        user=user,
        ip_address=serializer.context['request'].META.get('REMOTE_ADDR'),
    )
    
    return token
```

```python title="settings.py"
REST_AUTH = {
    'TOKEN_CREATOR': 'myapp.utils.custom_create_token',
}
```

---

## Custom Password Validation

### Password Change with Custom Validation

```python title="serializers.py"
from dj_rest_auth.serializers import PasswordChangeSerializer
from rest_framework import serializers

class CustomPasswordChangeSerializer(PasswordChangeSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        
        new_password = attrs.get('new_password1')
        
        # Custom rule: password cannot contain username
        if self.user.username.lower() in new_password.lower():
            raise serializers.ValidationError(
                {'new_password1': 'Password cannot contain your username.'}
            )
        
        # Custom rule: password cannot be similar to email
        email_local = self.user.email.split('@')[0].lower()
        if email_local in new_password.lower():
            raise serializers.ValidationError(
                {'new_password1': 'Password cannot contain your email address.'}
            )
        
        return attrs
```

### Password Reset with Custom Email

```python title="serializers.py"
from dj_rest_auth.serializers import PasswordResetSerializer

class CustomPasswordResetSerializer(PasswordResetSerializer):
    def get_email_options(self):
        return {
            'subject_template_name': 'emails/password_reset_subject.txt',
            'email_template_name': 'emails/password_reset_email.html',
            'html_email_template_name': 'emails/password_reset_email.html',
            'extra_email_context': {
                'company_name': 'My Company',
                'support_email': 'support@example.com',
            },
        }
```

---

## Custom Views

For more control, you can subclass the views directly:

```python title="views.py"
from dj_rest_auth.views import LoginView, LogoutView
from rest_framework.response import Response
from rest_framework import status

class CustomLoginView(LoginView):
    def post(self, request, *args, **kwargs):
        # Pre-login hook
        self.check_ip_whitelist(request)
        
        response = super().post(request, *args, **kwargs)
        
        # Post-login hook
        if response.status_code == status.HTTP_200_OK:
            self.log_successful_login(request)
        
        return response
    
    def check_ip_whitelist(self, request):
        # Custom IP checking logic
        pass
    
    def log_successful_login(self, request):
        # Custom logging logic
        pass


class CustomLogoutView(LogoutView):
    def logout(self, request):
        # Pre-logout hook
        self.cleanup_user_sessions(request.user)
        
        return super().logout(request)
    
    def cleanup_user_sessions(self, user):
        # Custom cleanup logic
        pass
```

```python title="urls.py"
from django.urls import path, include
from myapp.views import CustomLoginView, CustomLogoutView

urlpatterns = [
    path('api/auth/login/', CustomLoginView.as_view(), name='rest_login'),
    path('api/auth/logout/', CustomLogoutView.as_view(), name='rest_logout'),
    path('api/auth/', include('dj_rest_auth.urls')),  # Other endpoints
]
```

---

## Extending User Profile

A common pattern is to extend the user model with a profile:

### 1. Create Profile Model

```python title="models.py"
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
```

### 2. Create Profile Serializer

```python title="serializers.py"
from rest_framework import serializers
from dj_rest_auth.serializers import UserDetailsSerializer
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('phone_number', 'company', 'avatar', 'bio')

class CustomUserDetailsSerializer(UserDetailsSerializer):
    profile = UserProfileSerializer(source='profile')

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ('profile',)

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        
        # Update user fields
        instance = super().update(instance, validated_data)
        
        # Update profile fields
        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()
        
        return instance
```

### 3. Configure Settings

```python title="settings.py"
REST_AUTH = {
    'USER_DETAILS_SERIALIZER': 'myapp.serializers.CustomUserDetailsSerializer',
}
```

---

## Throttling

All dj-rest-auth views use the `dj_rest_auth` throttle scope. Configure rate limiting:

```python title="settings.py"
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'dj_rest_auth': '100/hour',
        'dj_rest_auth_login': '10/minute',  # Stricter for login
    },
}
```

To use a custom throttle scope for specific views:

```python title="views.py"
from dj_rest_auth.views import LoginView

class StrictLoginView(LoginView):
    throttle_scope = 'dj_rest_auth_login'
```
