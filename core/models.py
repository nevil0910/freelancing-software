from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

# Custom user model with an extra field for user type (client or freelancer)
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('client', 'Client'),
        ('freelancer', 'Freelancer'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='client')


# OTP Model for Password Reset
class PasswordResetOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)"""
        from django.conf import settings
        expiry_time = self.created_at + timedelta(minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10))
        return not self.is_used and timezone.now() < expiry_time

    def __str__(self):
        return f"OTP for {self.email} - {self.otp}"

    class Meta:
        ordering = ['-created_at']


# OTP Model for Signup Email Verification
class SignupOTP(models.Model):
    email = models.EmailField()
    username = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150, default='')
    last_name = models.CharField(max_length=150, default='')
    password = models.CharField(max_length=255)  # Will store hashed password
    user_type = models.CharField(max_length=10)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)"""
        from django.conf import settings
        expiry_time = self.created_at + timedelta(minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10))
        return not self.is_used and timezone.now() < expiry_time

    def __str__(self):
        return f"Signup OTP for {self.email} - {self.otp}"

    class Meta:
        ordering = ['-created_at']
