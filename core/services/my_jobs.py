from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Job


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
