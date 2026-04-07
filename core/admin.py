from django.contrib import admin

# Register your models here.
from .models import (
    CustomUser, Job, PasswordResetOTP, SignupOTP, EmailChangeOTP,
    ChatMessage, TypingStatus, JobSubmission, SubmissionFile, Earning, Review,
    FreelancerProfile, Post, PostLike, Comment
)

admin.site.register(CustomUser)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'budget', 'deadline', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'tagline', 'description', 'client__username', 'client__email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Job Information', {
            'fields': ('title', 'tagline', 'description', 'category', 'client')
        }),
        ('Budget & Timeline', {
            'fields': ('budget', 'deadline', 'required_freelancers')
        }),
        ('Status', {
            'fields': ('status', 'hired_freelancer', 'submitted_at', 'completed_at', 'auto_completed', 'created_at')
        }),
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'job', 'is_seen', 'created_at')
    list_filter = ('is_seen', 'created_at')
    search_fields = ('message', 'sender__username', 'job__title')


@admin.register(JobSubmission)
class JobSubmissionAdmin(admin.ModelAdmin):
    list_display = ('freelancer', 'job', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('freelancer__username', 'job__title')


@admin.register(SubmissionFile)
class SubmissionFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'file_type', 'submission')


@admin.register(Earning)
class EarningAdmin(admin.ModelAdmin):
    list_display = ('freelancer', 'job', 'amount', 'earned_at')
    list_filter = ('earned_at',)
    search_fields = ('freelancer__username', 'job__title')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('client', 'freelancer', 'job', 'rating', 'is_auto_completed', 'created_at')
    list_filter = ('rating', 'is_auto_completed', 'created_at')
    search_fields = ('client__username', 'freelancer__username', 'job__title')


admin.site.register(TypingStatus)


@admin.register(FreelancerProfile)
class FreelancerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'contact_number')
    search_fields = ('user__username', 'user__email')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('user__username', 'caption')


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username', 'text')


@admin.register(EmailChangeOTP)
class EmailChangeOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'new_email', 'otp', 'created_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'new_email', 'otp')
    readonly_fields = ('created_at',)
