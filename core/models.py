from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from cloudinary.models import CloudinaryField

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


# OTP Model for Email Change Verification
class EmailChangeOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_change_otps')
    new_email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)"""
        from django.conf import settings
        expiry_time = self.created_at + timedelta(minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10))
        return not self.is_used and timezone.now() < expiry_time

    def __str__(self):
        return f"Email Change OTP for {self.user.username} -> {self.new_email}"

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
    tagline = models.CharField(max_length=300, help_text='Brief summary of the job')
    description = models.TextField(help_text='Detailed job description')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    budget = models.DecimalField(max_digits=10, decimal_places=2, help_text='Budget in INR')
    deadline = models.DateField()
    required_freelancers = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='jobs')
    hired_freelancer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='hired_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    auto_completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.title} - {self.client.username}"

    class Meta:
        ordering = ['-created_at']


# Application Model for Freelancer Job Applications
class Application(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    )

    message = models.TextField(help_text='Cover letter or clarification message')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    freelancer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')

    def __str__(self):
        return f"{self.freelancer.username} applied to {self.job.title}"

    class Meta:
        ordering = ['-created_at']
        unique_together = [('job', 'freelancer')]


# Chat Message Model for job-specific messaging
class ChatMessage(models.Model):
    FILE_TYPE_CHOICES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('file', 'File'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField(blank=True, null=True)
    file_url = models.URLField(max_length=500, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, blank=True, null=True)
    is_seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat: {self.sender.username} on {self.job.title}"

    class Meta:
        ordering = ['created_at']


# Typing Status for real-time typing indicators
class TypingStatus(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='typing_statuses')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='typing_statuses')
    is_typing = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('job', 'user')]

    def __str__(self):
        return f"{self.user.username} typing in {self.job.title}: {self.is_typing}"


# Job Submission Model for freelancer work submissions
class JobSubmission(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='submissions')
    freelancer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='submissions')
    message = models.TextField(help_text='Submission message or notes')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission by {self.freelancer.username} for {self.job.title}"

    class Meta:
        ordering = ['-created_at']


# Submission File Model for files attached to submissions
class SubmissionFile(models.Model):
    FILE_TYPE_CHOICES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('file', 'File'),
    )

    submission = models.ForeignKey(JobSubmission, on_delete=models.CASCADE, related_name='files')
    file_url = models.URLField(max_length=500)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='file')

    def __str__(self):
        return f"{self.file_name} - {self.submission.job.title}"


# Earning Model for freelancer earnings per job
class Earning(models.Model):
    freelancer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='earnings')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='earnings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    earned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.freelancer.username} earned ₹{self.amount} from {self.job.title}"

    class Meta:
        ordering = ['-earned_at']


# Review Model for client reviews of freelancers
class Review(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='review')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_reviews')
    freelancer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.IntegerField(help_text='Rating from 1 to 5')
    comment = models.TextField(blank=True, null=True, help_text='Optional review comment')
    is_auto_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review: {self.client.username} → {self.freelancer.username} ({self.rating}★)"

    class Meta:
        ordering = ['-created_at']


# ── Profile ──────────────────────────────────────────────────────────────────
class FreelancerProfile(models.Model):
    """Extended profile for freelancer users."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='freelancer_profile')
    profile_photo = CloudinaryField('image', blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    rating = models.FloatField(default=0)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @classmethod
    def get_or_create_for(cls, user):
        """Get or create profile for a user."""
        profile, _ = cls.objects.get_or_create(user=user)
        return profile


# ── Post ─────────────────────────────────────────────────────────────────────
class Post(models.Model):
    """Portfolio post by a freelancer."""
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

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')
    media = CloudinaryField(resource_type='auto', blank=True, null=True) # Legacy single media
    caption = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post by {self.user.username} [{self.category}]"

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comments.count()

    @property
    def has_multiple_media(self):
        return self.media_files.count() > 1

    @property
    def first_media_info(self):
        first_media = self.media_files.first()
        if first_media:
            url = first_media.media.url if hasattr(first_media.media, 'url') else str(first_media.media)
            rt = getattr(first_media.media, 'resource_type', None)
            if not rt:
                rt = 'video' if any(url.lower().endswith(ext) for ext in ('.mp4', '.mov', '.webm')) else 'image'
            return {'url': url, 'resource_type': rt}
        elif self.media:
            url = self.media.url if hasattr(self.media, 'url') else str(self.media)
            rt = getattr(self.media, 'resource_type', None)
            if not rt:
                rt = 'video' if any(url.lower().endswith(ext) for ext in ('.mp4', '.mov', '.webm')) else 'image'
            return {'url': url, 'resource_type': rt}
        return None

    class Meta:
        ordering = ['-created_at']

# ── PostMedia (Carousel Support) ───────────────────────────────────────────────
class PostMedia(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media_files')
    media = CloudinaryField(resource_type='auto', blank=False, null=False)
    resource_type = models.CharField(max_length=10, default='image')  # 'image' or 'video'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Media for post #{self.post.id}"


# ── PostLike ──────────────────────────────────────────────────────────────────
class PostLike(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'post')]

    def __str__(self):
        return f"{self.user.username} liked post #{self.post.id}"


# ── Comment ───────────────────────────────────────────────────────────────────
class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='post_comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} commented on post #{self.post.id}"
