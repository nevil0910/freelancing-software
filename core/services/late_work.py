import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from ..models import Job
from .overdue import continue_late_work as continue_late_work_service
from .overdue import refund_overdue_job as refund_overdue_job_service


@login_required
@never_cache
def continue_late_work(request, job_id):
    """
    Client approves late work submission and allows freelancer to continue.
    Transitions job back to IN_PROGRESS.
    """
    if request.user.user_type != 'client':
        return JsonResponse({'success': False, 'error': 'Only clients can approve late work.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    job = get_object_or_404(Job, id=job_id, client=request.user)

    if job.status != 'OVERDUE':
        return JsonResponse({'success': False, 'error': 'Job must be in OVERDUE status.'}, status=400)

    try:
        job = continue_late_work_service(job_id)
        messages.success(request, 'Job reopened for late work.')
        return JsonResponse({'success': True, 'message': 'Late work approved. Job is now IN_PROGRESS.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@never_cache
def refund_overdue_job(request, job_id):
    """
    Client refunds the escrow for an overdue job and marks it as REFUNDED.
    """
    if request.user.user_type != 'client':
        return JsonResponse({'success': False, 'error': 'Only clients can refund jobs.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    job = get_object_or_404(Job, id=job_id, client=request.user)

    if job.status != 'OVERDUE':
        return JsonResponse({'success': False, 'error': 'Job must be in OVERDUE status.'}, status=400)

    try:
        job = refund_overdue_job_service(job_id)
        messages.success(request, 'Job refunded. Funds returned to your wallet.')
        return JsonResponse({'success': True, 'message': 'Job refunded successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
