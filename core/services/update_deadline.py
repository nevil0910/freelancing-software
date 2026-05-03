from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db import transaction
from ..models import Job
from ..forms import DeadlineForm


@login_required
@never_cache
def update_deadline(request, job_id):
    """
    Allows the client to update only the deadline of a job that is
    in progress, submitted, or overdue. Overdue jobs should also allow
    deadline updates so the client can reopen or extend the deadline.
    """
    if request.user.user_type != 'client':
        messages.error(request, 'Unauthorized.')
        return redirect('dashboard')

    job = get_object_or_404(
        Job,
        id=job_id,
        client=request.user,
        status__in=['IN_PROGRESS', 'SUBMITTED', 'OVERDUE']
    )

    if request.method == 'POST':
        with transaction.atomic():
            job = Job.objects.select_for_update().get(id=job.id)
            form = DeadlineForm(request.POST, instance=job)
            if form.is_valid():
                updated_job = form.save(commit=False)

                # If client updates deadline while OVERDUE, restore prior status
                # (e.g., IN_PROGRESS/SUBMITTED) and clear overdue markers.
                if updated_job.status == 'OVERDUE':
                    updated_job.status = updated_job.previous_status or 'IN_PROGRESS'
                    updated_job.previous_status = None
                    updated_job.overdue_at = None

                updated_job.save()
                messages.success(request, 'Deadline updated successfully.')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{error}')

    return redirect('job_view', job_id=job_id)
