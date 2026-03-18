from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Job


@login_required
@never_cache
def close_job(request, job_id):
    """
    View for clients to close a job.
    Only the job owner can close their job.
    Jobs can only be closed after COMPLETED status.
    """
    # Check if user is a client
    if request.user.user_type != 'client':
        messages.error(request, 'Only clients can close jobs.')
        return redirect('dashboard')

    # Get the job and ensure it belongs to the current user
    job = get_object_or_404(Job, id=job_id, client=request.user)

    if request.method == 'POST':
        if job.status not in ('COMPLETED', 'OPEN'):
            messages.error(request, 'This job cannot be closed in its current state.')
            return redirect('job_view', job_id=job.id)

        job.status = 'CLOSED'
        job.save()
        messages.success(request, f'Job "{job.title}" has been closed.')
        return redirect('my_jobs')

    return redirect('my_jobs')
