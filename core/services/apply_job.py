from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Job, Application


@login_required
@never_cache
def apply_job(request, job_id):
    """
    Freelancer submits an application for a job.
    Returns JSON for AJAX handling.
    """
    if request.user.user_type != 'freelancer':
        return JsonResponse({'success': False, 'error': 'Only freelancers can apply for jobs.'}, status=403)

    job = get_object_or_404(Job, id=job_id, status='OPEN')

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    message = request.POST.get('message', '').strip()
    if not message:
        return JsonResponse({'success': False, 'error': 'Please write a cover message before submitting.'})

    if Application.objects.filter(job=job, freelancer=request.user).exists():
        return JsonResponse({'success': False, 'error': 'You have already applied for this job.'})

    Application.objects.create(
        job=job,
        freelancer=request.user,
        message=message,
    )
    return JsonResponse({'success': True, 'message': 'Application submitted successfully!'})
