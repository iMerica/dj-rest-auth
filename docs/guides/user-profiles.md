# User Profiles & Common Patterns

This guide covers common patterns and frequently asked questions when using dj-rest-auth.

## Extending the User Model with a Profile

A common pattern is to create a separate profile model linked to the User model.

### 1. Create the Profile Model

```python title="models.py"
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    company_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

# Automatically create profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
```

### 2. Create the Serializers

```python title="serializers.py"
from rest_framework import serializers
from dj_rest_auth.serializers import UserDetailsSerializer
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('company_name', 'phone_number', 'avatar', 'bio')

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

### 4. Usage

**GET /api/auth/user/**

```json
{
    "pk": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile": {
        "company_name": "Acme Inc",
        "phone_number": "+1234567890",
        "avatar": "/media/avatars/john.jpg",
        "bio": "Software developer"
    }
}
```

**PATCH /api/auth/user/**

```json
{
    "first_name": "Johnny",
    "profile": {
        "company_name": "New Company"
    }
}
```

---

## Email Verification URL

### The Problem

You see this error when trying to verify emails:

```
Reverse for 'account_confirm_email' not found
```

Or the verification URL doesn't work as expected for your SPA.

### The Solution

The `account-confirm-email` URL is defined by dj-rest-auth but uses a placeholder view. You need to configure it for your use case.

#### For SPAs (Recommended)

```python title="urls.py"
from django.urls import path, re_path
from django.views.generic import TemplateView
from dj_rest_auth.registration.views import VerifyEmailView

urlpatterns = [
    # ... other urls ...
    
    # This URL is used in the email - redirect to your frontend
    re_path(
        r'^api/auth/account-confirm-email/(?P<key>[-:\w]+)/$',
        TemplateView.as_view(),
        name='account_confirm_email',
    ),
    
    # This endpoint verifies the key
    path(
        'api/auth/registration/verify-email/',
        VerifyEmailView.as_view(),
        name='rest_verify_email',
    ),
]
```

Configure allauth to use your frontend URL:

```python title="settings.py"
ACCOUNT_EMAIL_CONFIRMATION_URL = 'https://yourapp.com/verify-email/{key}'
```

Your frontend should:
1. Extract the `key` from the URL
2. POST it to `/api/auth/registration/verify-email/`

#### For Server-Side Rendering

Use allauth's built-in view:

```python title="urls.py"
from allauth.account.views import ConfirmEmailView

urlpatterns = [
    path(
        'api/auth/account-confirm-email/<str:key>/',
        ConfirmEmailView.as_view(),
        name='account_confirm_email',
    ),
]
```

---

## Password Reset URL

### The Problem

```
Reverse for 'password_reset_confirm' not found
```

### The Solution

Add the password reset confirm URL at the **top** of your urlpatterns:

```python title="urls.py"
from django.urls import path, include, re_path
from django.views.generic import TemplateView

urlpatterns = [
    # Must be before other URLs
    re_path(
        r'^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',
        TemplateView.as_view(template_name='password_reset_confirm.html'),
        name='password_reset_confirm',
    ),
    
    # Other URLs
    path('api/auth/', include('dj_rest_auth.urls')),
]
```

For SPAs, redirect to your frontend instead:

```python title="settings.py"
# In your email template or settings
PASSWORD_RESET_CONFIRM_URL = 'https://yourapp.com/reset-password/{uid}/{token}'
```

---

## Custom Registration Fields

Add extra fields to the registration form:

```python title="serializers.py"
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

class CustomRegisterSerializer(RegisterSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    company = serializers.CharField(required=False, allow_blank=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['first_name'] = self.validated_data.get('first_name', '')
        data['last_name'] = self.validated_data.get('last_name', '')
        data['company'] = self.validated_data.get('company', '')
        return data

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.save()
        
        # Save to profile if you have one
        if hasattr(user, 'profile'):
            user.profile.company = self.cleaned_data.get('company')
            user.profile.save()
        
        return user
```

```python title="settings.py"
REST_AUTH = {
    'REGISTER_SERIALIZER': 'myapp.serializers.CustomRegisterSerializer',
}
```

---

## Require Email Verification Before Login

### 1. Configure allauth

```python title="settings.py"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
```

### 2. Custom Login Serializer (Optional)

For a better error message:

```python title="serializers.py"
from dj_rest_auth.serializers import LoginSerializer
from rest_framework import serializers

class CustomLoginSerializer(LoginSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = attrs['user']
        
        if not user.emailaddress_set.filter(verified=True).exists():
            raise serializers.ValidationError(
                {'email': 'Please verify your email address before logging in.'}
            )
        
        return attrs
```

---

## Login with Email Instead of Username

```python title="settings.py"
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
```

---

## Refreshing Tokens on Activity

Keep users logged in while they're active by refreshing tokens:

```python title="middleware.py"
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

class TokenRefreshMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only for authenticated users with JWT
        if request.user.is_authenticated and hasattr(request, 'auth'):
            # Check if access token is close to expiring (e.g., < 5 minutes)
            # If so, set a new token in the response cookie
            pass
        
        return response
```

A simpler approach is using `ROTATE_REFRESH_TOKENS` in SimpleJWT:

```python title="settings.py"
SIMPLE_JWT = {
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

---

## Multiple User Types

Handle different user types (e.g., customers vs. vendors):

### Using Groups

```python title="serializers.py"
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth.models import Group

class CustomerRegisterSerializer(RegisterSerializer):
    def save(self, request):
        user = super().save(request)
        customer_group = Group.objects.get(name='Customers')
        user.groups.add(customer_group)
        return user

class VendorRegisterSerializer(RegisterSerializer):
    business_name = serializers.CharField(required=True)
    
    def save(self, request):
        user = super().save(request)
        vendor_group = Group.objects.get(name='Vendors')
        user.groups.add(vendor_group)
        # Create vendor profile
        VendorProfile.objects.create(
            user=user,
            business_name=self.validated_data['business_name']
        )
        return user
```

### Separate Endpoints

```python title="views.py"
from dj_rest_auth.registration.views import RegisterView
from .serializers import CustomerRegisterSerializer, VendorRegisterSerializer

class CustomerRegisterView(RegisterView):
    serializer_class = CustomerRegisterSerializer

class VendorRegisterView(RegisterView):
    serializer_class = VendorRegisterSerializer
```

```python title="urls.py"
urlpatterns = [
    path('api/auth/register/customer/', CustomerRegisterView.as_view()),
    path('api/auth/register/vendor/', VendorRegisterView.as_view()),
]
```

---

## Rate Limiting Login Attempts

Protect against brute force attacks:

```python title="settings.py"
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'dj_rest_auth': '100/hour',
        'login': '5/minute',
    },
}
```

```python title="views.py"
from dj_rest_auth.views import LoginView

class ThrottledLoginView(LoginView):
    throttle_scope = 'login'
```

```python title="urls.py"
from .views import ThrottledLoginView

urlpatterns = [
    path('api/auth/login/', ThrottledLoginView.as_view(), name='rest_login'),
    path('api/auth/', include('dj_rest_auth.urls')),
]
```
