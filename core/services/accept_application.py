from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Application


@login_required
@never_cache
def accept_application(request, application_id):
    """
    Client accepts a freelancer application.
    Also sets the job status to IN_PROGRESS.
    Returns JSON for AJAX handling.
    """
    if request.user.user_type != 'client':
        return JsonResponse({'success': False, 'error': 'Unauthorized.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    application = get_object_or_404(Application, id=application_id, job__client=request.user)
    application.status = 'ACCEPTED'
    application.save()

    # Set the job to IN_PROGRESS only when required seats are filled.
    job = application.job
    if job.status == 'OPEN':
        accepted_count = job.applications.filter(status='ACCEPTED').count()
        if accepted_count >= max(1, job.required_freelancers):
            job.status = 'IN_PROGRESS'
            if not job.hired_freelancer:
                job.hired_freelancer = application.freelancer
            job.save()

    if job.status == 'IN_PROGRESS':
        message = 'Application accepted. Job is now In Progress.'
    else:
        pending = max(1, job.required_freelancers) - job.applications.filter(status='ACCEPTED').count()
        message = f'Application accepted. Need {pending} more accepted application(s) to start.'

    return JsonResponse({'success': True, 'status': 'ACCEPTED', 'message': message})
