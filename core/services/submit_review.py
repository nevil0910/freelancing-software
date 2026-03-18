import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Job, Review, Application


@login_required
@never_cache
def submit_review(request, job_id):
    """
    Client submits a review (rating + optional comment) for a completed job.
    """
    if request.user.user_type != 'client':
        return JsonResponse({'success': False, 'error': 'Only clients can submit reviews.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    job = get_object_or_404(Job, id=job_id, client=request.user)

    if job.status not in ('COMPLETED', 'CLOSED'):
        return JsonResponse({'success': False, 'error': 'Job must be completed to review.'}, status=400)

    # Check if review already exists
    if hasattr(job, 'review'):
        return JsonResponse({'success': False, 'error': 'Review already submitted for this job.'}, status=400)

    try:
        rating = int(request.POST.get('rating', 0))
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid rating.'}, status=400)

    if rating < 1 or rating > 5:
        return JsonResponse({'success': False, 'error': 'Rating must be between 1 and 5.'}, status=400)

    comment = request.POST.get('comment', '').strip()

    # Resolve actual freelancer (hired_freelancer or accepted application)
    freelancer = job.hired_freelancer
    if not freelancer:
        acc_app = Application.objects.filter(job=job, status='ACCEPTED').select_related('freelancer').first()
        freelancer = acc_app.freelancer if acc_app else None

    if not freelancer:
        return JsonResponse({'success': False, 'error': 'No freelancer assigned to this job.'}, status=400)

    Review.objects.create(
        job=job,
        client=request.user,
        freelancer=freelancer,
        rating=rating,
        comment=comment if comment else None,
        is_auto_completed=job.auto_completed
    )

    return JsonResponse({
        'success': True,
        'message': 'Review submitted successfully!'
    })


@login_required
@never_cache
def get_pending_reviews(request):
    """
    Returns list of completed jobs that the client hasn't reviewed yet.
    Used to trigger review popup once per login.
    """
    if request.user.user_type != 'client':
        return JsonResponse({'pending_reviews': []})

    # Find completed/closed jobs by this client that lack a review
    completed_jobs = Job.objects.filter(
        client=request.user,
        status__in=['COMPLETED', 'CLOSED'],
    ).exclude(
        review__isnull=False
    )

    pending = []
    for job in completed_jobs:
        freelancer = job.hired_freelancer
        if not freelancer:
            acc_app = Application.objects.filter(job=job, status='ACCEPTED').select_related('freelancer').first()
            freelancer = acc_app.freelancer if acc_app else None
        if freelancer:
            pending.append({
                'job_id': job.id,
                'title': job.title,
                'auto_completed': job.auto_completed,
                'freelancer': freelancer.username
            })

    return JsonResponse({'pending_reviews': pending})
