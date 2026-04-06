import json
import logging
import cloudinary.uploader
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils import timezone
from ..models import Job, JobSubmission, SubmissionFile


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


@login_required
@never_cache
def submit_work(request, job_id):
    """
    Freelancer submits work for a job.
    Accepts files (uploaded to Cloudinary) and a message.
    Sets job status to SUBMITTED.
    """
    if request.user.user_type != 'freelancer':
        return JsonResponse({'success': False, 'error': 'Only freelancers can submit work.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    from ..models import Application
    job = get_object_or_404(Job, id=job_id)

    # Check authorization: must be hired_freelancer OR have an accepted application
    is_authorized = False
    if job.hired_freelancer and job.hired_freelancer == request.user:
        is_authorized = True
    elif Application.objects.filter(job=job, freelancer=request.user, status='ACCEPTED').exists():
        is_authorized = True

    if not is_authorized:
        return JsonResponse({'success': False, 'error': 'You are not assigned to this job.'}, status=403)

    if job.status not in ('IN_PROGRESS', 'SUBMITTED'):
        return JsonResponse({'success': False, 'error': 'Job is not in a submittable state.'}, status=400)

    message = request.POST.get('message', '').strip()
    files = request.FILES.getlist('files')

    if not message and not files:
        return JsonResponse({'success': False, 'error': 'Please provide a message or files.'}, status=400)

    # Create submission record
    submission = JobSubmission.objects.create(
        job=job,
        freelancer=request.user,
        message=message
    )

    # Upload files to Cloudinary
    uploaded_files = []
    for f in files:
        file_type = get_file_type(f.name)
        try:
            resource_type = 'video' if file_type == 'video' else ('image' if file_type == 'image' else 'raw')
            result = cloudinary.uploader.upload(
                f,
                resource_type=resource_type,
                type='upload',  # Ensures public access
                folder=f'freelancehub/submissions/{job_id}'
            )
            sf = SubmissionFile.objects.create(
                submission=submission,
                file_url=result['secure_url'],
                file_name=f.name,
                file_type=file_type
            )
            uploaded_files.append({
                'id': sf.id,
                'url': sf.file_url,
                'name': sf.file_name,
                'type': sf.file_type
            })
        except Exception as e:
            logging.error(f'Cloudinary upload failed for {f.name}: {e}')
            # Return error immediately so user knows upload failed
            return JsonResponse({
                'success': False,
                'error': f'Failed to upload file "{f.name}": {str(e)}'
            }, status=500)

    # Update job status
    job.status = 'SUBMITTED'
    job.submitted_at = timezone.now()
    job.save()

    return JsonResponse({
        'success': True,
        'message': 'Work submitted successfully!',
        'submission_id': submission.id,
        'files': uploaded_files
    })
