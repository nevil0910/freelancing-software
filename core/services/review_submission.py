from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils import timezone
from ..models import Job, Earning
from .escrow import release_escrow_for_job


@login_required
@never_cache
def review_submission(request, job_id):
    """
    Client reviews freelancer's submission.
    Actions:
      - 'accept' → COMPLETED, create Earning
      - 'request_changes' → back to IN_PROGRESS
    """
    if request.user.user_type != 'client':
        return JsonResponse({'success': False, 'error': 'Only clients can review submissions.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    job = get_object_or_404(Job, id=job_id, client=request.user)

    if job.status != 'SUBMITTED':
        return JsonResponse({'success': False, 'error': 'Job is not in submitted state.'}, status=400)

    action = request.POST.get('action', '')

    if action == 'accept':
        job.status = 'COMPLETED'
        job.completed_at = timezone.now()
        job.save()

        # Create earning record for the freelancer
        from ..models import Application
        freelancer = job.hired_freelancer
        if not freelancer:
            acc_app = Application.objects.filter(job=job, status='ACCEPTED').select_related('freelancer').first()
            freelancer = acc_app.freelancer if acc_app else None

        if freelancer:
            released = release_escrow_for_job(job, freelancer)
            if not released:
                Earning.objects.get_or_create(
                    freelancer=freelancer,
                    job=job,
                    defaults={'amount': job.budget}
                )

        return JsonResponse({
            'success': True,
            'message': 'Work accepted! Job is now completed.',
            'new_status': 'COMPLETED'
        })

    elif action == 'request_changes':
        job.status = 'IN_PROGRESS'
        job.submitted_at = None
        job.save()

        return JsonResponse({
            'success': True,
            'message': 'Changes requested. Freelancer can resubmit.',
            'new_status': 'IN_PROGRESS'
        })

    return JsonResponse({'success': False, 'error': 'Invalid action.'}, status=400)
