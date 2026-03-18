from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db.models import Avg
from ..models import Job, Application, JobSubmission, Review
from ..forms import JobForm, DeadlineForm


@login_required
@never_cache
def job_view(request, job_id):
    """
    Unified job detail view for both freelancers and clients.
    Now includes chat, submission, and review context.
    """
    user = request.user

    # Determine back URL using the HTTP Referer header
    referer = request.META.get('HTTP_REFERER', '')
    if '/my-proposals/' in referer:
        back_url = '/my-proposals/'
    elif '/active-jobs/' in referer:
        back_url = '/active-jobs/'
    elif user.user_type == 'client':
        back_url = '/my-jobs/'
    else:
        back_url = '/browse-jobs/'

    if user.user_type == 'client':
        job = get_object_or_404(Job, id=job_id, client=user)
        applications = job.applications.select_related('freelancer').all()
        has_applied = False
        user_application = None
        if job.status in ('IN_PROGRESS', 'SUBMITTED'):
            form = None
            deadline_form = DeadlineForm(instance=job)
        else:
            form = JobForm(instance=job)
            deadline_form = None
    else:
        job = get_object_or_404(Job, id=job_id)
        applications = None
        form = None
        deadline_form = None
        try:
            user_application = Application.objects.get(job=job, freelancer=user)
            has_applied = True
        except Application.DoesNotExist:
            user_application = None
            has_applied = False

    # Get submissions for this job
    submissions = JobSubmission.objects.filter(job=job).prefetch_related('files').order_by('-created_at')
    latest_submission = submissions.first()

    # Check if review exists
    has_review = Review.objects.filter(job=job).exists()

    # Check if current user can access chat
    # Works via hired_freelancer OR accepted application (for older jobs)
    can_chat = False
    if job.status in ('IN_PROGRESS', 'SUBMITTED', 'COMPLETED'):
        if user == job.client:
            can_chat = True
        elif job.hired_freelancer and user == job.hired_freelancer:
            can_chat = True
        elif user.user_type == 'freelancer' and Application.objects.filter(
            job=job, freelancer=user, status='ACCEPTED'
        ).exists():
            can_chat = True

    # Is the freelancer the one working on this job?
    is_hired_freelancer = False
    if user.user_type == 'freelancer':
        if job.hired_freelancer and job.hired_freelancer == user:
            is_hired_freelancer = True
        elif Application.objects.filter(job=job, freelancer=user, status='ACCEPTED').exists():
            is_hired_freelancer = True

    # Get freelancer average rating
    freelancer_rating = None
    # Get the actual hired freelancer (via field or accepted application)
    actual_freelancer = job.hired_freelancer
    if not actual_freelancer:
        acc_app = Application.objects.filter(job=job, status='ACCEPTED').select_related('freelancer').first()
        actual_freelancer = acc_app.freelancer if acc_app else None

    if actual_freelancer:
        avg = Review.objects.filter(freelancer=actual_freelancer).aggregate(avg_rating=Avg('rating'))
        count = Review.objects.filter(freelancer=actual_freelancer).count()
        if count > 0:
            freelancer_rating = {
                'average': round(avg['avg_rating'], 1),
                'count': count
            }

    context = {
        'job': job,
        'applications': applications,
        'has_applied': has_applied,
        'user_application': user_application,
        'form': form,
        'deadline_form': deadline_form,
        'back_url': back_url,
        'submissions': submissions,
        'latest_submission': latest_submission,
        'has_review': has_review,
        'can_chat': can_chat,
        'is_hired_freelancer': is_hired_freelancer,
        'freelancer_rating': freelancer_rating,
        'actual_freelancer': actual_freelancer,
    }
    return render(request, 'core/job_view.html', context)


