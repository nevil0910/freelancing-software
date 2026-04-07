from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.contrib import messages
from django.db.models import Avg
from ..models import Job, Review


@login_required
@never_cache
def review_proposals(request):
    if request.user.user_type != 'client':
        messages.error(request, 'Only clients can view proposals.')
        return redirect('dashboard')

    jobs = Job.objects.filter(client=request.user).order_by('-created_at')
    for job in jobs:
        job.applications_count = job.applications.filter(status='PENDING').count()

    return render(request, 'core/review_proposals.html', {'jobs': jobs})


@login_required
@never_cache
@require_GET
def review_job_applications(request, job_id):
    if request.user.user_type != 'client':
        return JsonResponse({'success': False, 'error': 'Unauthorized.'}, status=403)

    job = get_object_or_404(Job, id=job_id, client=request.user)
    applications = job.applications.select_related('freelancer').order_by('-created_at')

    freelancer_ids = [app.freelancer_id for app in applications]
    rating_rows = (
        Review.objects
        .filter(freelancer_id__in=freelancer_ids)
        .values('freelancer_id')
        .annotate(avg_rating=Avg('rating'))
    )
    rating_map = {r['freelancer_id']: round(r['avg_rating'], 1) for r in rating_rows if r['avg_rating'] is not None}

    items = []
    for app in applications:
        items.append({
            'id': app.id,
            'status': app.status,
            'status_display': app.get_status_display(),
            'message': app.message,
            'created_at': app.created_at.strftime('%b %d, %Y'),
            'freelancer_username': app.freelancer.username,
            'avatar_initial': app.freelancer.avatar_initial,
            'avatar_url': app.freelancer.profile_photo_url,
            'review_avg': rating_map.get(app.freelancer_id, 0),
            'profile_url': f'/profile/{app.freelancer.username}/',
        })

    pending_count = sum(1 for a in items if a['status'] == 'PENDING')
    return JsonResponse({
        'success': True,
        'job': {'id': job.id, 'title': job.title},
        'pending_count': pending_count,
        'applications': items,
    })
