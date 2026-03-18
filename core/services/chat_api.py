import json
import cloudinary.uploader
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db.models import Q, Max, Count, Subquery, OuterRef
from ..models import Job, ChatMessage, TypingStatus, Application


def get_file_type(filename):
    """Determine file type based on extension."""
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    image_exts = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'}
    video_exts = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv', 'wmv'}
    if ext in image_exts:
        return 'image'
    elif ext in video_exts:
        return 'video'
    return 'file'


def can_access_chat(user, job):
    """Check if user has access to chat for this job."""
    if job.status == 'CLOSED':
        return False
    if user == job.client:
        return True
    if job.hired_freelancer and user == job.hired_freelancer:
        return True
    # Always check accepted application (handles old jobs where hired_freelancer was not set)
    if Application.objects.filter(job=job, freelancer=user, status='ACCEPTED').exists():
        return True
    return False


@login_required
@never_cache
def send_message(request, job_id):
    """Send a chat message (text and/or file) in a job conversation."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method.'}, status=400)

    job = get_object_or_404(Job, id=job_id)
    if not can_access_chat(request.user, job):
        return JsonResponse({'success': False, 'error': 'Access denied.'}, status=403)

    message_text = request.POST.get('message', '').strip()
    file = request.FILES.get('file')

    if not message_text and not file:
        return JsonResponse({'success': False, 'error': 'Message or file required.'}, status=400)

    file_url = None
    file_name = None
    file_type = None

    if file:
        file_type = get_file_type(file.name)
        try:
            resource_type = 'video' if file_type == 'video' else ('image' if file_type == 'image' else 'raw')
            result = cloudinary.uploader.upload(
                file,
                resource_type=resource_type,
                folder=f'freelancehub/chat/{job_id}'
            )
            file_url = result['secure_url']
            file_name = file.name
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'File upload failed: {str(e)}'}, status=500)

    msg = ChatMessage.objects.create(
        job=job,
        sender=request.user,
        message=message_text if message_text else None,
        file_url=file_url,
        file_name=file_name,
        file_type=file_type
    )

    # Clear typing status
    TypingStatus.objects.filter(job=job, user=request.user).update(is_typing=False)

    return JsonResponse({
        'success': True,
        'message': {
            'id': msg.id,
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'text': msg.message,
            'file_url': msg.file_url,
            'file_name': msg.file_name,
            'file_type': msg.file_type,
            'is_seen': msg.is_seen,
            'created_at': msg.created_at.isoformat(),
        }
    })


@login_required
@never_cache
def get_messages(request, job_id):
    """Fetch chat messages for a job. Supports ?after=<msg_id> for polling."""
    job = get_object_or_404(Job, id=job_id)
    if not can_access_chat(request.user, job):
        return JsonResponse({'success': False, 'error': 'Access denied.'}, status=403)

    after_id = request.GET.get('after', 0)
    try:
        after_id = int(after_id)
    except (ValueError, TypeError):
        after_id = 0

    messages_qs = ChatMessage.objects.filter(job=job)
    if after_id > 0:
        messages_qs = messages_qs.filter(id__gt=after_id)

    messages_list = []
    for msg in messages_qs[:100]:
        messages_list.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'text': msg.message,
            'file_url': msg.file_url,
            'file_name': msg.file_name,
            'file_type': msg.file_type,
            'is_seen': msg.is_seen,
            'created_at': msg.created_at.isoformat(),
        })

    return JsonResponse({'success': True, 'messages': messages_list})


@login_required
@never_cache
def mark_seen(request, job_id):
    """Mark all messages in a job chat as seen by the current user."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method.'}, status=400)

    job = get_object_or_404(Job, id=job_id)
    if not can_access_chat(request.user, job):
        return JsonResponse({'success': False, 'error': 'Access denied.'}, status=403)

    # Mark messages sent by other users as seen
    updated = ChatMessage.objects.filter(
        job=job,
        is_seen=False
    ).exclude(sender=request.user).update(is_seen=True)

    return JsonResponse({'success': True, 'marked': updated})


@login_required
@never_cache
def set_typing(request, job_id):
    """Update typing status for current user in a job chat."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method.'}, status=400)

    job = get_object_or_404(Job, id=job_id)
    if not can_access_chat(request.user, job):
        return JsonResponse({'success': False, 'error': 'Access denied.'}, status=403)

    is_typing = request.POST.get('is_typing', 'false') == 'true'

    TypingStatus.objects.update_or_create(
        job=job,
        user=request.user,
        defaults={'is_typing': is_typing}
    )

    return JsonResponse({'success': True})


@login_required
@never_cache
def get_typing(request, job_id):
    """Check if the other user is typing in a job chat."""
    job = get_object_or_404(Job, id=job_id)
    if not can_access_chat(request.user, job):
        return JsonResponse({'success': False, 'error': 'Access denied.'}, status=403)

    # Get typing status of other users (not current user)
    # Only consider typing if updated within last 5 seconds
    threshold = timezone.now() - timezone.timedelta(seconds=5)
    typing_users = TypingStatus.objects.filter(
        job=job,
        is_typing=True,
        updated_at__gte=threshold
    ).exclude(user=request.user).values_list('user__username', flat=True)

    return JsonResponse({
        'success': True,
        'typing_users': list(typing_users)
    })


@login_required
@never_cache
def get_chat_list(request):
    """
    Get list of all job chats accessible to the current user.
    Returns chats grouped by status (ongoing vs completed).
    """
    user = request.user

    # Find all jobs where user is client or hired_freelancer or has accepted application
    if user.user_type == 'client':
        jobs = Job.objects.filter(
            client=user,
            status__in=['IN_PROGRESS', 'SUBMITTED', 'COMPLETED']
        ).select_related('hired_freelancer')
    else:
        # Include jobs where hired_freelancer=user OR has accepted application
        job_ids_via_app = Application.objects.filter(
            freelancer=user,
            status='ACCEPTED',
            job__status__in=['IN_PROGRESS', 'SUBMITTED', 'COMPLETED']
        ).values_list('job_id', flat=True)
        jobs = Job.objects.filter(
            id__in=job_ids_via_app
        ).select_related('client', 'hired_freelancer')

    chat_list = []
    for job in jobs:
        # Get last message
        last_msg = ChatMessage.objects.filter(job=job).order_by('-created_at').first()

        # Count unread messages (not sent by current user, not seen)
        unread_count = ChatMessage.objects.filter(
            job=job,
            is_seen=False
        ).exclude(sender=user).count()

        # Determine the other person (client gets freelancer, freelancer gets client)
        if user.user_type == 'client':
            # Try hired_freelancer first, then accepted application
            other_user = job.hired_freelancer
            if not other_user:
                acc_app = Application.objects.filter(
                    job=job, status='ACCEPTED'
                ).select_related('freelancer').first()
                other_user = acc_app.freelancer if acc_app else None
        else:
            other_user = job.client

        # Format: "Job Title - First Name"
        if other_user:
            other_display_name = other_user.first_name if other_user.first_name else other_user.username
            other_initial = other_display_name[0].upper()
        else:
            other_display_name = 'Unknown'
            other_initial = '?'

        # Chat label: "Job Title - Other Person First Name"
        chat_label = f"{job.title[:30]} - {other_display_name}"

        chat_list.append({
            'job_id': job.id,
            'job_title': job.title,
            'chat_label': chat_label,
            'job_status': job.status,
            'other_user': other_display_name,
            'other_initial': other_initial,
            'unread_count': unread_count,
            'last_message': {
                'text': last_msg.message if last_msg else None,
                'file_name': last_msg.file_name if last_msg else None,
                'sender': last_msg.sender.username if last_msg else None,
                'created_at': last_msg.created_at.isoformat() if last_msg else None,
            } if last_msg else None
        })

    # Sort by last message time (most recent first)
    chat_list.sort(
        key=lambda x: x['last_message']['created_at'] if x.get('last_message') else '',
        reverse=True
    )

    return JsonResponse({'success': True, 'chats': chat_list})


@login_required
@never_cache
def get_unread_count(request):
    """Get total unread message count for the floating chat badge."""
    user = request.user

    if user.user_type == 'client':
        jobs_filter = Q(job__client=user)
    else:
        jobs_filter = Q(job__hired_freelancer=user)

    total_unread = ChatMessage.objects.filter(
        jobs_filter,
        is_seen=False,
        job__status__in=['IN_PROGRESS', 'SUBMITTED', 'COMPLETED']
    ).exclude(sender=user).count()

    # Split by tab
    ongoing_unread = ChatMessage.objects.filter(
        jobs_filter,
        is_seen=False,
        job__status__in=['IN_PROGRESS', 'SUBMITTED']
    ).exclude(sender=user).count()

    completed_unread = ChatMessage.objects.filter(
        jobs_filter,
        is_seen=False,
        job__status='COMPLETED'
    ).exclude(sender=user).count()

    return JsonResponse({
        'success': True,
        'total': total_unread,
        'ongoing': ongoing_unread,
        'completed': completed_unread
    })
