from django.utils import timezone
from datetime import timedelta
from ..models import Job, Earning
from .escrow import release_escrow_for_job


def check_auto_complete():
    """
    Check all SUBMITTED jobs and auto-complete any that have been
    waiting for client review for more than 3 days.
    Called on each authenticated page load via context processor.
    """
    three_days_ago = timezone.now() - timedelta(days=3)
    
    jobs_to_complete = Job.objects.filter(
        status='SUBMITTED',
        submitted_at__isnull=False,
        submitted_at__lte=three_days_ago
    )
    
    for job in jobs_to_complete:
        job.status = 'COMPLETED'
        job.completed_at = timezone.now()
        job.auto_completed = True
        job.save()
        
        # Create earning record
        if job.hired_freelancer:
            released = release_escrow_for_job(job, job.hired_freelancer)
            if not released:
                Earning.objects.get_or_create(
                    freelancer=job.hired_freelancer,
                    job=job,
                    defaults={'amount': job.budget}
                )
