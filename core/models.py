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


# Job Model for Client Job Postings
class Job(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
        ('COMPLETED', 'Completed'),
        ('CLOSED', 'Closed'),
    )
    
    CATEGORY_CHOICES = (
        ('web_dev', 'Web Development'),
        ('mobile_dev', 'Mobile Development'),
        ('design', 'Graphic Design'),
        ('writing', 'Content Writing'),
        ('marketing', 'Digital Marketing'),
        ('data_entry', 'Data Entry'),
        ('seo', 'SEO & Analytics'),
        ('video_edit', 'Video Editing'),
        ('ai_ml', 'AI & Machine Learning'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    budget = models.DecimalField(max_digits=10, decimal_places=2, help_text='Budget in INR')
    deadline = models.DateField()
    required_freelancers = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.client.username}"
    
    class Meta:
        ordering = ['-created_at']
