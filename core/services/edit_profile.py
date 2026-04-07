from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.db import transaction
from ..models import CustomUser, FreelancerProfile, EmailChangeOTP
from .email import generate_otp, send_email_change_otp, send_email_async


@login_required
def edit_profile_view(request):
    """Render the edit profile page."""
    return render(request, 'core/edit_profile.html')


@login_required
@require_POST
def send_email_change_otp_view(request):
    """Send OTP to new email address for verification."""
    user = request.user
    new_email = request.POST.get('email', '').strip()
    
    # Validate new email
    if not new_email:
        return JsonResponse({'success': False, 'error': 'Email is required.'}, status=400)
    
    # Check if email is same as current
    if new_email == user.email:
        return JsonResponse({'success': False, 'error': 'This is already your current email.'}, status=400)
    
    # Validate email format
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(new_email)
    except ValidationError:
        return JsonResponse({'success': False, 'error': 'Invalid email format.'}, status=400)
    
    # Check if email is already in use
    if CustomUser.objects.filter(email=new_email).exists():
        return JsonResponse({'success': False, 'error': 'Email already in use.'}, status=400)
    
    # Generate OTP
    otp = generate_otp()
    
    # Save OTP record
    EmailChangeOTP.objects.create(
        user=user,
        new_email=new_email,
        otp=otp
    )
    
    # Send OTP via email asynchronously
    send_email_async(send_email_change_otp, new_email, user.username, otp)
    
    return JsonResponse({
        'success': True,
        'message': 'OTP sent to your new email address. Please check your inbox.'
    })


@login_required
@require_POST
def verify_email_change_otp_view(request):
    """Verify OTP and update email."""
    user = request.user
    otp_entered = request.POST.get('otp', '').strip()
    
    if not otp_entered:
        return JsonResponse({'success': False, 'error': 'OTP is required.'}, status=400)
    
    # Find valid OTP
    try:
        otp_record = EmailChangeOTP.objects.filter(
            user=user,
            otp=otp_entered,
            is_used=False
        ).latest('created_at')
        
        if not otp_record.is_valid():
            return JsonResponse({'success': False, 'error': 'OTP has expired. Please request a new one.'}, status=400)
        
        # Mark OTP as used
        otp_record.is_used = True
        otp_record.save()
        
        # Return success with new email (don't update yet - will update in main form submission)
        return JsonResponse({
            'success': True,
            'message': 'Email verified successfully!',
            'new_email': otp_record.new_email
        })
        
    except EmailChangeOTP.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid OTP. Please try again.'}, status=400)


@login_required
@require_POST
def update_profile(request):
    """Update user profile information."""
    user = request.user
    
    # Get form data
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    contact_number = request.POST.get('contact_number', '').strip()
    email_verified = request.POST.get('email_verified', 'false') == 'true'
    
    # Validate required fields
    if not first_name:
        return JsonResponse({'success': False, 'error': 'First name is required.'}, status=400)
    
    if not last_name:
        return JsonResponse({'success': False, 'error': 'Last name is required.'}, status=400)
    
    if not username:
        return JsonResponse({'success': False, 'error': 'Username is required.'}, status=400)
    
    if not email:
        return JsonResponse({'success': False, 'error': 'Email is required.'}, status=400)
    
    # Validate username uniqueness (exclude current user)
    if username != user.username:
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Username already taken.'}, status=400)
    
    # Email change requires OTP verification
    if email != user.email:
        if not email_verified:
            return JsonResponse({'success': False, 'error': 'Please verify your new email address first.'}, status=400)
        
        # Double-check OTP was verified
        try:
            otp_record = EmailChangeOTP.objects.filter(
                user=user,
                new_email=email,
                is_used=True
            ).latest('created_at')
        except EmailChangeOTP.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Email not verified. Please request OTP again.'}, status=400)
    
    # Validate username format (alphanumeric, underscores, hyphens)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return JsonResponse({'success': False, 'error': 'Username can only contain letters, numbers, underscores, and hyphens.'}, status=400)
    
    # Validate email format
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'success': False, 'error': 'Invalid email format.'}, status=400)
    
    # Update user fields
    try:
        with transaction.atomic():
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.email = email
            user.save()
            
            # Update contact number if user is freelancer
            if user.user_type == 'freelancer':
                profile = FreelancerProfile.get_or_create_for(user)
                profile.contact_number = contact_number if contact_number else None
                profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully!',
            'data': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'email': user.email,
                'contact_number': contact_number if user.user_type == 'freelancer' else None
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Failed to update profile: {str(e)}'}, status=500)

