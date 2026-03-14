from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Job
from ..forms import JobForm


@login_required
@never_cache
def update_job(request, job_id):
    """
    Client updates an existing job's details.
    """
    if request.user.user_type != 'client':
        messages.error(request, 'Only clients can update jobs.')
        return redirect('dashboard')

    job = get_object_or_404(Job, id=job_id, client=request.user)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.replace("_", " ").title()}: {error}')

    return redirect('job_view', job_id=job_id)
