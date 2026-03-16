from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Job
from ..forms import DeadlineForm


@login_required
@never_cache
def update_deadline(request, job_id):
    """
    Allows the client to update only the deadline of an IN_PROGRESS job.
    """
    if request.user.user_type != 'client':
        messages.error(request, 'Unauthorized.')
        return redirect('dashboard')

    job = get_object_or_404(Job, id=job_id, client=request.user, status='IN_PROGRESS')

    if request.method == 'POST':
        form = DeadlineForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Deadline updated successfully.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')

    return redirect('job_view', job_id=job_id)
