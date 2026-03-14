from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Job, Application
from ..forms import JobForm


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
