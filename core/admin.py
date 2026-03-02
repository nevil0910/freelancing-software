from django.contrib import admin

# Register your models here.
from .models import CustomUser, Job, PasswordResetOTP, SignupOTP

admin.site.register(CustomUser)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'budget', 'deadline', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'client__username', 'client__email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Job Information', {
            'fields': ('title', 'description', 'client')
        }),
        ('Budget & Timeline', {
            'fields': ('budget', 'deadline', 'required_freelancers')
        }),
        ('Status', {
            'fields': ('status', 'created_at')
        }),
    )
