from django.utils import timezone
from django.db import transaction
from ..models import Job


def check_overdue():
    """
    Mark IN_PROGRESS jobs as OVERDUE when their deadline has passed.
    This is intended to be called from a context processor on authenticated
    page loads (acceptable for a college project) so overdue status is kept
    reasonably up-to-date without a background worker.
    """
    today = timezone.now().date()
    overdue_jobs = Job.objects.filter(status='IN_PROGRESS', deadline__lt=today)

    for job in overdue_jobs:
        job.previous_status = job.status
        job.status = 'OVERDUE'
        job.overdue_at = timezone.now()
        job.save(update_fields=['previous_status', 'status', 'overdue_at'])

    return overdue_jobs.count()


def continue_late_work(job_id):
    """
    Client approves late work and job transitions back to IN_PROGRESS
    (freelancer can continue working past deadline).
    """
    job = Job.objects.get(id=job_id)
    if job.status != 'OVERDUE':
        raise ValueError("Job must be in OVERDUE status to continue late work")
    
    job.status = 'IN_PROGRESS'
    job.previous_status = None
    job.overdue_at = None
    job.save(update_fields=['status', 'previous_status', 'overdue_at'])
    return job


def refund_overdue_job(job_id):
    """
    Client refunds the escrow for an overdue job and marks it as REFUNDED.
    Calls the escrow service to refund the budget back to the client.
    """
    from .escrow import refund_escrow_for_job
    
    with transaction.atomic():
        job = Job.objects.select_for_update().get(id=job_id)
        if job.status != 'OVERDUE':
            raise ValueError("Job must be in OVERDUE status to refund")
        
        # Refund escrow
        refund_escrow_for_job(job)
        
        # Mark job as REFUNDED
        job.status = 'REFUNDED'
        job.previous_status = None
        job.save(update_fields=['status', 'previous_status'])
    
    return job
