from .services.email import send_email_async, generate_otp, send_signup_otp_email, send_otp_email
from .services.auth import home, signup, login_view, logoutUser, dashboard, verify_signup_otp
from .services.password_reset import forgot_password, verify_otp, reset_password
from .services.availability import check_username_availability, check_email_availability
from .services.post_job import post_job
from .services.my_jobs import my_jobs
from .services.close_job import close_job
from .services.job_view import job_view
from .services.apply_job import apply_job
from .services.update_job import update_job
from .services.accept_application import accept_application
from .services.reject_application import reject_application
from .services.browse_jobs import browse_jobs
from .services.my_proposals import my_proposals
from .services.active_jobs import active_jobs
from .services.update_deadline import update_deadline

