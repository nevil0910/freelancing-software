from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Application


@login_required
@never_cache
def active_jobs(request):
    """
    View for freelancers to see their active (IN_PROGRESS) jobs.
    An active job = the freelancer has an ACCEPTED application on an IN_PROGRESS job.
    """
    if request.user.user_type != 'freelancer':
        messages.error(request, 'Only freelancers can view active jobs.')
        return redirect('dashboard')

    # Get accepted applications on IN_PROGRESS jobs for the current freelancer
    applications = (
        Application.objects
        .filter(freelancer=request.user, status='ACCEPTED', job__status='IN_PROGRESS')
        .select_related('job', 'job__client')
        .order_by('-updated_at')
    )

    context = {
        'applications': applications,
    }
    return render(request, 'core/active_jobs.html', context)
