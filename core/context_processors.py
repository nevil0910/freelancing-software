from django.conf import settings
from .services.auto_complete import check_auto_complete
from .models import ChatMessage, Job, Review
from django.db.models import Q


def app_name(request):
    return {'APP_NAME': settings.APP_NAME}


def chat_context(request):
    if not request.user.is_authenticated:
        return {}

    check_auto_complete()
    user = request.user

    # Total unread messages (client or freelancer)
    if user.user_type == 'client':
        jobs_filter = Q(job__client=user)
    else:
        jobs_filter = Q(job__hired_freelancer=user)

    total_unread = ChatMessage.objects.filter(
        jobs_filter,
        is_seen=False,
        job__status__in=['IN_PROGRESS', 'SUBMITTED', 'COMPLETED']
    ).exclude(sender=user).count()

    # Pending review count (client only)
    # Includes jobs where hired_freelancer is null but an accepted application exists
    pending_review_count = 0
    if user.user_type == 'client':
        from .models import Application
        # Jobs that are completed/closed and have no review yet
        unreviewed_jobs = Job.objects.filter(
            client=user,
            status__in=['COMPLETED', 'CLOSED'],
        ).exclude(
            id__in=Review.objects.values_list('job_id', flat=True)
        )
        # Among those, count how many have an assignable freelancer
        jobs_with_freelancer = unreviewed_jobs.filter(
            hired_freelancer__isnull=False
        ).count()
        jobs_via_app = unreviewed_jobs.filter(
            hired_freelancer__isnull=True,
            applications__status='ACCEPTED'
        ).distinct().count()
        pending_review_count = jobs_with_freelancer + jobs_via_app

    return {
        'total_unread_messages': total_unread,
        'pending_review_count': pending_review_count,
    }

