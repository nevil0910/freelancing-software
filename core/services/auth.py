from django.shortcuts import render, redirect
from django.contrib.auth import logout, login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.hashers import make_password
from ..models import CustomUser, SignupOTP
from .email import generate_otp, send_signup_otp_email, send_email_async
from ..validators import UsernameValidate


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
        username = UsernameValidate.normalize_username(request.POST.get('username'))
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')

        if not username or not password or not email or not first_name or not last_name:
            return render(request, 'core/signup.html', {'error': 'Please provide all required fields'})

        # Validate username format on backend (cannot rely on JS only)
        try:
            UsernameValidate.validate_username_format(username)
        except ValidationError as e:
            return render(request, 'core/signup.html', {'error': ' '.join(e.messages)})

        # Validate email format and require 2+ char TLD like example.com
        try:
            validate_email(email)
        except ValidationError:
            return render(request, 'core/signup.html', {'error': 'Please enter a valid email address'})

        import re
        if not re.match(r'^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$', email):
            return render(request, 'core/signup.html', {'error': 'Email domain must end with at least 2 letters'})

        # Check if username already exists
        if CustomUser.objects.filter(username__iexact=username).exists():
            return render(request, 'core/signup.html', {'error': 'Username already taken'})

        # Check if email already exists
        if CustomUser.objects.filter(email__iexact=email).exists():
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
        raw = request.POST.get('username')
        username_or_email = raw.lower()
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
            if user.is_blocked:
                return render(request, 'core/login.html', {'error': 'Your account is blocked. Contact support.'})
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
    Render dashboard based on user type with real statistics.
    """
    from ..models import Job, Application, Earning
    from django.db.models import Sum

    user = request.user

    if user.is_superuser:
        from ..models import Escrow, RefundRequest, Wallet
        from django.db.models import Sum
        platform_wallet = Wallet.objects.filter(wallet_type='PLATFORM').first()
        context = {
            'platform_balance': platform_wallet.balance if platform_wallet else 0,
            'total_commission': Escrow.objects.filter(status='RELEASED').aggregate(total=Sum('commission_amount'))['total'] or 0,
            'pending_escrows': Escrow.objects.filter(status='FUNDED').count(),
            'pending_refunds': RefundRequest.objects.filter(status='PENDING').count(),
        }
        return render(request, 'core/admin_dashboard.html', context)
    if user.user_type == 'client':
        posted_jobs = Job.objects.filter(client=user).count()
        total_spent = Earning.objects.filter(job__client=user).aggregate(total=Sum('amount'))['total'] or 0
        active_projects = Job.objects.filter(client=user, status='IN_PROGRESS').count()
        completed_projects = Job.objects.filter(client=user, status__in=['COMPLETED', 'CLOSED']).count()

        context = {
            'posted_jobs': posted_jobs,
            'total_spent': total_spent,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
        }
        return render(request, 'core/client_dashboard.html', context)
    else:
        active_jobs = Job.objects.filter(
            hired_freelancer=user, status='IN_PROGRESS'
        ).count()
        submitted_proposals = Application.objects.filter(
            freelancer=user, status='PENDING'
        ).count()
        total_earnings = Earning.objects.filter(
            freelancer=user
        ).aggregate(total=Sum('amount'))['total'] or 0
        completed_jobs = Job.objects.filter(
            hired_freelancer=user, status__in=['COMPLETED', 'CLOSED']
        ).count()

        context = {
            'active_jobs': active_jobs,
            'submitted_proposals': submitted_proposals,
            'total_earnings': total_earnings,
            'completed_jobs': completed_jobs,
        }
        return render(request, 'core/freelancer_dashboard.html', context)


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
