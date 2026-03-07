from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.contrib.auth import logout, login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from .models import CustomUser, PasswordResetOTP, SignupOTP, Job, Application
from .forms import JobForm
import random
import string
import threading


# Helper function to send emails asynchronously
def send_email_async(email_function, *args, **kwargs):
    """Send email in a background thread to avoid blocking the request"""
    thread = threading.Thread(target=email_function, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()

def home(request):
    """
    Render the homepage. Redirect to dashboard if user is already logged in.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')


@never_cache
def signup(request):
    # Redirect to dashboard if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')

        if not username or not password or not email or not first_name or not last_name:
            return render(request, 'core/signup.html', {'error': 'Please provide all required fields'})

        # Check if username already exists
        if CustomUser.objects.filter(username=username).exists():
            return render(request, 'core/signup.html', {'error': 'Username already taken'})
        
        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            return render(request, 'core/signup.html', {'error': 'Email already taken'})

        # Validate password against Django's password validators
        try:
            validate_password(password)
        except ValidationError as e:
            error_messages = ' '.join(e.messages)
            return render(request, 'core/signup.html', {'error': error_messages})

        # Generate OTP for email verification
        otp = generate_otp()
        
        # Hash the password before storing
        hashed_password = make_password(password)
        
        # Save signup data temporarily with OTP
        SignupOTP.objects.create(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=hashed_password,
            user_type=user_type,
            otp=otp
        )
        
        # Send OTP via email asynchronously (non-blocking)
        send_email_async(send_signup_otp_email, email, username, otp)
        
        # Store email in session for next step and redirect immediately
        request.session['signup_email'] = email
        return redirect('verify_signup_otp')

    return render(request, 'core/signup.html')


@never_cache
def login_view(request):
    # Redirect to dashboard if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')

        # Try to authenticate with username first
        user = authenticate(username=username_or_email, password=password)
        
        # If authentication failed, try with email
        if user is None:
            try:
                # Check if input is an email and get the user
                user_obj = CustomUser.objects.get(email=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except CustomUser.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, 'core/login.html', {'error': 'Invalid credentials'})

    return render(request, 'core/login.html')

# Logout View
@never_cache
def logoutUser(request):
    #user = request.user  # Get the current logged-in user

    logout(request)

     # Optional: Delete the user permanently from the database
    '''if user:
        user.delete()'''

    messages.success(request, "You have successfully logged out!")
    return redirect("login")


@login_required
@never_cache
def dashboard(request):
    """
    Render dashboard based on user type.
    """
    if request.user.user_type == 'client':
        return render(request, 'core/client_dashboard.html')
    else:
        return render(request, 'core/freelancer_dashboard.html')


@never_cache
def verify_signup_otp(request):
    """Verify OTP for signup email verification"""
    email = request.session.get('signup_email')
    
    if not email:
        messages.error(request, 'Session expired. Please sign up again.')
        return redirect('signup')
    
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        
        if not otp_entered:
            return render(request, 'core/verify_otp.html', {'error': 'Please enter the OTP', 'signup_mode': True})
        
        # Find valid OTP
        try:
            otp_record = SignupOTP.objects.filter(
                email=email,
                otp=otp_entered,
                is_used=False
            ).latest('created_at')
            
            if otp_record.is_valid():
                # Mark OTP as used
                otp_record.is_used = True
                otp_record.save()
                
                # Create the user now
                user = CustomUser.objects.create_user(
                    username=otp_record.username,
                    email=otp_record.email,
                    password=None,  # Don't hash again
                    user_type=otp_record.user_type,
                    first_name=otp_record.first_name,
                    last_name=otp_record.last_name
                )
                # Set the already-hashed password
                user.password = otp_record.password
                user.save()
                
                # Clear session
                del request.session['signup_email']
                
                # Redirect to success page
                return render(request, 'core/success_redirect.html', {
                    'title': 'Signup Successful!',
                    'message': 'Your account has been created successfully.'
                })
            else:
                return render(request, 'core/verify_otp.html', {
                    'error': 'OTP has expired. Please sign up again.',
                    'signup_mode': True
                })
        
        except SignupOTP.DoesNotExist:
            return render(request, 'core/verify_otp.html', {
                'error': 'Invalid OTP. Please try again.',
                'signup_mode': True
            })
    
    return render(request, 'core/verify_otp.html', {'signup_mode': True})


# ============= FORGOT PASSWORD SYSTEM =============

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def send_signup_otp_email(email, username, otp):
    """Send OTP for signup verification"""
    subject = f'{settings.APP_NAME} - Email Verification'
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f7;
            }}
            .email-container {{
                max-width: 600px;
                margin: 40px auto;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }}
            .email-header {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 40px 30px;
                text-align: center;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            }}
            .email-header h1 {{
                color: #ffffff;
                font-size: 32px;
                margin: 0;
                font-weight: 700;
            }}
            .email-body {{
                background: #ffffff;
                padding: 50px 40px;
            }}
            .email-body h2 {{
                color: #333333;
                font-size: 24px;
                margin-bottom: 20px;
            }}
            .email-body p {{
                color: #666666;
                font-size: 16px;
                line-height: 1.6;
                margin-bottom: 30px;
            }}
            .otp-container {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 30px;
                text-align: center;
                margin: 30px 0;
            }}
            .otp-code {{
                font-size: 48px;
                font-weight: 700;
                color: #ffffff;
                letter-spacing: 8px;
                margin: 10px 0;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            }}
            .otp-label {{
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            .warning-box {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px 20px;
                margin: 25px 0;
                border-radius: 4px;
            }}
            .warning-box p {{
                color: #856404;
                margin: 0;
                font-size: 14px;
            }}
            .email-footer {{
                background: #f8f9fa;
                padding: 30px 40px;
                text-align: center;
                color: #999999;
                font-size: 14px;
                line-height: 1.6;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <h1>{settings.APP_NAME}</h1>
            </div>
            <div class="email-body">
                <h2>🎉 Welcome {username}!</h2>
                <p>Thank you for signing up! To complete your registration, please verify your email address using the OTP code below:</p>
                
                <div class="otp-container">
                    <div class="otp-label">Your Verification Code</div>
                    <div class="otp-code">{otp}</div>
                </div>
                
                <div class="warning-box">
                    <p><strong>⚠️ Important:</strong> This OTP will expire in {settings.OTP_EXPIRY_MINUTES} minutes. If you didn't create an account, please ignore this email.</p>
                </div>
                
                <p><strong>Note:</strong> This email might be in your spam/junk folder. Please check there if you don't see it in your inbox.</p>
            </div>
            <div class="email-footer">
                <p>This email was sent by {settings.APP_NAME}</p>
                <p>© 2026 {settings.APP_NAME}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    {settings.APP_NAME} - Email Verification
    
    Welcome {username}!
    
    Your Verification Code: {otp}
    
    This OTP will expire in {settings.OTP_EXPIRY_MINUTES} minutes.
    
    If you didn't create an account, please ignore this email.
    """
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=html_message,
        fail_silently=False,
    )


def send_otp_email(email, otp):
    """Send OTP via email with modern HTML template"""
    subject = f'{settings.APP_NAME} - Password Reset OTP'
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f7;
            }}
            .email-container {{
                max-width: 600px;
                margin: 40px auto;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }}
            .email-header {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 40px 30px;
                text-align: center;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            }}
            .email-header h1 {{
                color: #ffffff;
                font-size: 32px;
                margin: 0;
                font-weight: 700;
            }}
            .email-body {{
                background: #ffffff;
                padding: 50px 40px;
            }}
            .email-body h2 {{
                color: #333333;
                font-size: 24px;
                margin-bottom: 20px;
            }}
            .email-body p {{
                color: #666666;
                font-size: 16px;
                line-height: 1.6;
                margin-bottom: 30px;
            }}
            .otp-container {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 30px;
                text-align: center;
                margin: 30px 0;
            }}
            .otp-code {{
                font-size: 48px;
                font-weight: 700;
                color: #ffffff;
                letter-spacing: 8px;
                margin: 10px 0;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            }}
            .otp-label {{
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            .warning-box {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px 20px;
                margin: 25px 0;
                border-radius: 4px;
            }}
            .warning-box p {{
                color: #856404;
                margin: 0;
                font-size: 14px;
            }}
            .email-footer {{
                background: #f8f9fa;
                padding: 30px 40px;
                text-align: center;
                color: #999999;
                font-size: 14px;
                line-height: 1.6;
            }}
            .email-footer a {{
                color: #667eea;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <h1>{settings.APP_NAME}</h1>
            </div>
            <div class="email-body">
                <h2>🔐 Password Reset Request</h2>
                <p>Hello!</p>
                <p>We received a request to reset your password. Use the OTP code below to complete your password reset:</p>
                
                <div class="otp-container">
                    <div class="otp-label">Your OTP Code</div>
                    <div class="otp-code">{otp}</div>
                </div>
                
                <div class="warning-box">
                    <p><strong>⚠️ Important:</strong> This OTP will expire in {settings.OTP_EXPIRY_MINUTES} minutes. Do not share this code with anyone.</p>
                </div>
                
                <p>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
            </div>
            <div class="email-footer">
                <p>This email was sent by {settings.APP_NAME}</p>
                <p>© 2026 {settings.APP_NAME}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    {settings.APP_NAME} - Password Reset OTP
    
    Your OTP Code: {otp}
    
    This OTP will expire in {settings.OTP_EXPIRY_MINUTES} minutes.
    
    If you didn't request a password reset, please ignore this email.
    """
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=html_message,
        fail_silently=False,
    )

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
                'success': 'If an account with this email exists, you will receive an OTP shortly.'
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


# ============= AVAILABILITY CHECK API =============

def check_username_availability(request):
    """API endpoint to check if username is available"""
    if request.method != 'POST':
        return JsonResponse({'available': False, 'error': 'Invalid request method'})
    
    username = request.POST.get('username', '').strip()
    
    if not username:
        return JsonResponse({'available': False, 'error': 'Username is required'})
    
    # Check if username exists in CustomUser
    user_exists = CustomUser.objects.filter(username=username).exists()
    
    available = not user_exists
    
    return JsonResponse({'available': available})


def check_email_availability(request):
    """API endpoint to check if email is available"""
    if request.method != 'POST':
        return JsonResponse({'available': False, 'error': 'Invalid request method'})
    
    email = request.POST.get('email', '').strip()
    
    if not email:
        return JsonResponse({'available': False, 'error': 'Email is required'})
    
    # Check if email exists in CustomUser
    user_exists = CustomUser.objects.filter(email=email).exists()
    
    available = not user_exists
    
    return JsonResponse({'available': available})


# ============================================
# Job Management Views
# ============================================

@login_required
@never_cache
def post_job(request):
    """
    View for clients to post a new job.
    Only accessible by users with 'client' user_type.
    """
    # Check if user is a client
    if request.user.user_type != 'client':
        messages.error(request, 'Only clients can post jobs.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.client = request.user
            job.status = 'OPEN'
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('my_jobs')
        else:
            # Form has validation errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = JobForm()
    
    return render(request, 'core/post_job.html', {'form': form})


@login_required
@never_cache
def my_jobs(request):
    """
    View for clients to see all their posted jobs.
    Only accessible by users with 'client' user_type.
    """
    # Check if user is a client
    if request.user.user_type != 'client':
        messages.error(request, 'Only clients can view posted jobs.')
        return redirect('dashboard')
    
    # Get all jobs posted by the current client with real application counts
    jobs = Job.objects.filter(client=request.user).order_by('-created_at')

    for job in jobs:
        job.applications_count = job.applications.count()
    
    return render(request, 'core/my_jobs.html', {'jobs': jobs})


@login_required
@never_cache
def close_job(request, job_id):
    """
    View for clients to close a job.
    Only the job owner can close their job.
    """
    # Check if user is a client
    if request.user.user_type != 'client':
        messages.error(request, 'Only clients can close jobs.')
        return redirect('dashboard')
    
    # Get the job and ensure it belongs to the current user
    job = get_object_or_404(Job, id=job_id, client=request.user)
    
    if request.method == 'POST':
        job.status = 'CLOSED'
        job.save()
        messages.success(request, f'Job "{job.title}" has been closed.')
        return redirect('my_jobs')
    
    return redirect('my_jobs')


# ============================================
# Job View (shared by freelancers and clients)
# ============================================

@login_required
@never_cache
def job_view(request, job_id):
    """
    Unified job detail view for both freelancers and clients.
    - Freelancers: can view any OPEN job and apply.
    - Clients: can view and manage only their own jobs.
    """
    user = request.user

    if user.user_type == 'client':
        job = get_object_or_404(Job, id=job_id, client=user)
        applications = job.applications.select_related('freelancer').all()
        has_applied = False
        user_application = None
        form = JobForm(instance=job)
    else:
        job = get_object_or_404(Job, id=job_id)
        applications = None
        form = None
        try:
            user_application = Application.objects.get(job=job, freelancer=user)
            has_applied = True
        except Application.DoesNotExist:
            user_application = None
            has_applied = False

    context = {
        'job': job,
        'applications': applications,
        'has_applied': has_applied,
        'user_application': user_application,
        'form': form,
    }
    return render(request, 'core/job_view.html', context)


@login_required
@never_cache
def apply_job(request, job_id):
    """
    Freelancer submits an application for a job.
    Returns JSON for AJAX handling.
    """
    if request.user.user_type != 'freelancer':
        return JsonResponse({'success': False, 'error': 'Only freelancers can apply for jobs.'}, status=403)

    job = get_object_or_404(Job, id=job_id, status='OPEN')

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    message = request.POST.get('message', '').strip()
    if not message:
        return JsonResponse({'success': False, 'error': 'Please write a cover message before submitting.'})

    if Application.objects.filter(job=job, freelancer=request.user).exists():
        return JsonResponse({'success': False, 'error': 'You have already applied for this job.'})

    Application.objects.create(
        job=job,
        freelancer=request.user,
        message=message,
    )
    return JsonResponse({'success': True, 'message': 'Application submitted successfully!'})


@login_required
@never_cache
def update_job(request, job_id):
    """
    Client updates an existing job's details.
    """
    if request.user.user_type != 'client':
        messages.error(request, 'Only clients can update jobs.')
        return redirect('dashboard')

    job = get_object_or_404(Job, id=job_id, client=request.user)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.replace("_", " ").title()}: {error}')

    return redirect('job_view', job_id=job_id)


@login_required
@never_cache
def accept_application(request, application_id):
    """
    Client accepts a freelancer application.
    Returns JSON for AJAX handling.
    """
    if request.user.user_type != 'client':
        return JsonResponse({'success': False, 'error': 'Unauthorized.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    application = get_object_or_404(Application, id=application_id, job__client=request.user)
    application.status = 'ACCEPTED'
    application.save()
    return JsonResponse({'success': True, 'status': 'ACCEPTED', 'message': 'Application accepted.'})


@login_required
@never_cache
def reject_application(request, application_id):
    """
    Client rejects a freelancer application.
    Returns JSON for AJAX handling.
    """
    if request.user.user_type != 'client':
        return JsonResponse({'success': False, 'error': 'Unauthorized.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    application = get_object_or_404(Application, id=application_id, job__client=request.user)
    application.status = 'REJECTED'
    application.save()
    return JsonResponse({'success': True, 'status': 'REJECTED', 'message': 'Application rejected.'})


# ============================================
# Browse Jobs (Freelancer)
# ============================================

@login_required
@never_cache
def browse_jobs(request):
    """
    View for freelancers to browse and search available jobs.
    Only accessible by users with 'freelancer' user_type.
    Supports filtering by category, search by client, and sorting.
    """
    # Check if user is a freelancer
    if request.user.user_type != 'freelancer':
        messages.error(request, 'Only freelancers can browse jobs.')
        return redirect('dashboard')
    
    # Get all OPEN jobs
    jobs = Job.objects.filter(status='OPEN').select_related('client')
    
    # Get filter parameters from POST (form uses method="post")
    category = request.POST.get('category', '')
    search = request.POST.get('search', '')
    sort = request.POST.get('sort', 'newest')
    
    # Apply category filter
    if category:
        jobs = jobs.filter(category=category)
    
    # Apply search filter (client username)
    if search:
        jobs = jobs.filter(client__username__icontains=search)
    
    # Apply sorting
    if sort == 'newest':
        jobs = jobs.order_by('-created_at')
    elif sort == 'budget_low':
        jobs = jobs.order_by('budget')
    elif sort == 'budget_high':
        jobs = jobs.order_by('-budget')
    elif sort == 'deadline_earliest':
        jobs = jobs.order_by('deadline')
    elif sort == 'deadline_latest':
        jobs = jobs.order_by('-deadline')
    else:
        jobs = jobs.order_by('-created_at')
    
    # Get category choices for the filter dropdown
    categories = Job.CATEGORY_CHOICES
    
    context = {
        'jobs': jobs,
        'categories': categories,
        'selected_category': category,
        'search_query': search,
        'selected_sort': sort,
    }
    
    return render(request, 'core/browse_jobs.html', context)

