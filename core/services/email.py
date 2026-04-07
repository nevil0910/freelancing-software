from django.core.mail import send_mail
from django.conf import settings
import random
import string
import threading


# Helper function to send emails asynchronously
def send_email_async(email_function, *args, **kwargs):
    """Send email in a background thread to avoid blocking the request"""
    thread = threading.Thread(target=email_function, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()


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
                font-size: 36px;
                font-weight: 700;
                color: #ffffff;
                letter-spacing: 6px;
                margin: 10px 0;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
                word-break: break-all;
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
                font-size: 36px;
                font-weight: 700;
                color: #ffffff;
                letter-spacing: 6px;
                margin: 10px 0;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
                word-break: break-all;
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


def send_email_change_otp(email, username, otp):
    """Send OTP for email change verification"""
    subject = f'{settings.APP_NAME} - Email Change Verification'

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
                font-size: 36px;
                font-weight: 700;
                color: #ffffff;
                letter-spacing: 6px;
                margin: 10px 0;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
                word-break: break-all;
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
                <h2>📧 Email Change Verification</h2>
                <p>Hello {username}!</p>
                <p>We received a request to change your email address. To verify this new email address, please use the OTP code below:</p>

                <div class="otp-container">
                    <div class="otp-label">Your Verification Code</div>
                    <div class="otp-code">{otp}</div>
                </div>

                <div class="warning-box">
                    <p><strong>⚠️ Important:</strong> This OTP will expire in {settings.OTP_EXPIRY_MINUTES} minutes. If you didn't request this change, please contact support immediately.</p>
                </div>

                <p>After verification, your email address will be updated successfully.</p>
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
    {settings.APP_NAME} - Email Change Verification

    Hello {username}!

    Your Email Change Verification Code: {otp}

    This OTP will expire in {settings.OTP_EXPIRY_MINUTES} minutes.

    If you didn't request this change, please contact support.
    """

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=html_message,
        fail_silently=False,
    )

