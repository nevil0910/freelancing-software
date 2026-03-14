from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from ..models import CustomUser, PasswordResetOTP
from .email import generate_otp, send_otp_email, send_email_async


@never_cache
def forgot_password(request):
    """Step 1: Request OTP for password reset"""
    if request.method == 'POST':
        email = request.POST.get('email')

        if not email:
            return render(request, 'core/forgot_password.html', {'error': 'Please provide your email address'})

        # Check if user exists
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            # Don't reveal if email exists or not for security
            return render(request, 'core/forgot_password.html', {
                'success': 'Account with this email does not exists, Sign Up first.'
            })

        # Generate OTP
        otp = generate_otp()

        # Save OTP to database
        PasswordResetOTP.objects.create(email=email, otp=otp)

        # Send OTP via email asynchronously (non-blocking)
        send_email_async(send_otp_email, email, otp)

        # Store email in session for next step and redirect immediately
        request.session['reset_email'] = email
        return redirect('verify_otp')

    return render(request, 'core/forgot_password.html')

@never_cache
def verify_otp(request):
    """Step 2: Verify OTP"""
    email = request.session.get('reset_email')

    if not email:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('forgot_password')

    if request.method == 'POST':
        otp_entered = request.POST.get('otp')

        if not otp_entered:
            return render(request, 'core/verify_otp.html', {'error': 'Please enter the OTP'})

        # Find valid OTP
        try:
            otp_record = PasswordResetOTP.objects.filter(
                email=email,
                otp=otp_entered,
                is_used=False
            ).latest('created_at')

            if otp_record.is_valid():
                # Mark OTP as used
                otp_record.is_used = True
                otp_record.save()

                # Store verified status in session
                request.session['otp_verified'] = True
                return redirect('reset_password')
            else:
                return render(request, 'core/verify_otp.html', {'error': 'OTP has expired. Please request a new one.'})

        except PasswordResetOTP.DoesNotExist:
            return render(request, 'core/verify_otp.html', {'error': 'Invalid OTP. Please try again.'})

    return render(request, 'core/verify_otp.html')

@never_cache
def reset_password(request):
    """Step 3: Reset password after OTP verification"""
    email = request.session.get('reset_email')
    otp_verified = request.session.get('otp_verified')

    if not email or not otp_verified:
        messages.error(request, 'Unauthorized access. Please complete OTP verification first.')
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not new_password or not confirm_password:
            return render(request, 'core/reset_password.html', {'error': 'Please provide both password fields'})

        if new_password != confirm_password:
            return render(request, 'core/reset_password.html', {'error': 'Passwords do not match'})

        # Validate password
        try:
            validate_password(new_password)
        except ValidationError as e:
            error_messages = ' '.join(e.messages)
            return render(request, 'core/reset_password.html', {'error': error_messages})

        # Update password
        try:
            user = CustomUser.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            # Clear session data
            del request.session['reset_email']
            del request.session['otp_verified']

            # Redirect to success page with countdown
            return render(request, 'core/success_redirect.html', {
                'title': 'Password Reset Successful!',
                'message': 'Your password has been changed successfully.'
            })

        except CustomUser.DoesNotExist:
            return render(request, 'core/reset_password.html', {'error': 'User not found'})

    return render(request, 'core/reset_password.html')
