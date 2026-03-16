from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Job, Application
from ..forms import JobForm, DeadlineForm


@login_required
@never_cache
def job_view(request, job_id):
    """
    Unified job detail view for both freelancers and clients.
    - Freelancers: can view any job and see their application status.
    - Clients: can view and manage only their own jobs.
    """
    user = request.user

    # Determine back URL using the HTTP Referer header (no query params in URL)
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
        # Full form for OPEN jobs, deadline-only for IN_PROGRESS
        if job.status == 'IN_PROGRESS':
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

    context = {
        'job': job,
        'applications': applications,
        'has_applied': has_applied,
        'user_application': user_application,
        'form': form,
        'deadline_form': deadline_form,
        'back_url': back_url,
    }
    return render(request, 'core/job_view.html', context)

