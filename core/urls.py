from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('verify-signup-otp/', views.verify_signup_otp, name='verify_signup_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    # Job Management URLs
    path('post-job/', views.post_job, name='post_job'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('close-job/<int:job_id>/', views.close_job, name='close_job'),
    path('browse-jobs/', views.browse_jobs, name='browse_jobs'),
    path('job/<int:job_id>/', views.job_view, name='job_view'),
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('job/<int:job_id>/update/', views.update_job, name='update_job'),
    path('application/<int:application_id>/accept/', views.accept_application, name='accept_application'),
    path('application/<int:application_id>/reject/', views.reject_application, name='reject_application'),
    path('my-proposals/', views.my_proposals, name='my_proposals'),
    path('active-jobs/', views.active_jobs, name='active_jobs'),
    path('job/<int:job_id>/update-deadline/', views.update_deadline, name='update_deadline'),

    # Submission & Review URLs
    path('job/<int:job_id>/submit-work/', views.submit_work, name='submit_work'),
    path('job/<int:job_id>/review-submission/', views.review_submission, name='review_submission'),
    path('job/<int:job_id>/submit-review/', views.submit_review, name='submit_review'),
    path('earnings/', views.earnings_view, name='earnings'),

    # Chat API URLs
    path('job/<int:job_id>/chat/send/', views.send_message, name='chat_send'),
    path('job/<int:job_id>/chat/messages/', views.get_messages, name='chat_messages'),
    path('job/<int:job_id>/chat/mark-seen/', views.mark_seen, name='chat_mark_seen'),
    path('job/<int:job_id>/chat/typing/', views.set_typing, name='chat_set_typing'),
    path('job/<int:job_id>/chat/typing-status/', views.get_typing, name='chat_get_typing'),
    path('api/chat-list/', views.get_chat_list, name='chat_list'),
    path('api/unread-count/', views.get_unread_count, name='unread_count'),
    path('api/pending-reviews/', views.get_pending_reviews, name='pending_reviews'),
    path('api/chat-file/<int:message_id>/download/', views.download_chat_file, name='download_chat_file'),

    # API endpoints
    path('check-username/', views.check_username_availability, name='check_username'),
    path('check-email/', views.check_email_availability, name='check_email'),

    # Profile & Posts URLs
    path('profile/add-post/', views.add_post, name='add_post'),
    path('profile/update-photo/', views.update_profile_photo, name='update_profile_photo'),
    path('profile/delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    path('api/post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('api/post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('api/profile/<str:username>/posts/', views.filter_posts, name='filter_posts'),
]
