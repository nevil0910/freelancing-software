from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from ..models import CustomUser, Escrow, RefundRequest, WalletTransaction
from .escrow import refund_escrow_for_job, get_platform_wallet


def _is_admin(user):
    return user.is_authenticated and user.is_superuser


@login_required
@never_cache
def admin_dashboard(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    platform_wallet = get_platform_wallet()
    total_commission = Escrow.objects.filter(status='RELEASED').aggregate(total=Sum('commission_amount'))['total'] or 0
    pending_escrows = Escrow.objects.filter(status='FUNDED').count()
    pending_refunds = RefundRequest.objects.filter(status='PENDING').count()
    blocked_users = CustomUser.objects.filter(is_blocked=True).count()
    context = {
        'platform_balance': platform_wallet.balance,
        'total_commission': total_commission,
        'pending_escrows': pending_escrows,
        'pending_refunds': pending_refunds,
        'blocked_users': blocked_users,
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
@never_cache
def admin_users(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    users = CustomUser.objects.exclude(id=request.user.id).order_by('-date_joined')
    return render(request, 'core/admin_users.html', {'users': users})


@login_required
@require_POST
def admin_toggle_block_user(request, user_id):
    if not _is_admin(request.user):
        return redirect('dashboard')
    target = get_object_or_404(CustomUser, id=user_id)
    if target.is_superuser:
        messages.error(request, 'Admin account cannot be blocked.')
        return redirect('admin_users')
    if target.is_blocked:
        target.is_blocked = False
        target.blocked_reason = ''
        target.blocked_at = None
        target.blocked_by = None
        target.save()
        messages.success(request, f'{target.username} unblocked.')
    else:
        target.is_blocked = True
        target.blocked_reason = request.POST.get('reason', '').strip()[:255]
        target.blocked_at = timezone.now()
        target.blocked_by = request.user
        target.save()
        messages.success(request, f'{target.username} blocked.')
    return redirect('admin_users')


@login_required
@never_cache
def admin_refunds(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    refunds = RefundRequest.objects.select_related('job', 'client').all()
    return render(request, 'core/admin_refunds.html', {'refunds': refunds})


@login_required
@require_POST
def admin_refund_action(request, refund_id):
    if not _is_admin(request.user):
        return redirect('dashboard')
    refund = get_object_or_404(RefundRequest, id=refund_id)
    action = request.POST.get('action')
    note = request.POST.get('note', '').strip()
    refund.reviewed_by = request.user
    refund.reviewed_at = timezone.now()
    refund.admin_note = note
    if action == 'approve':
        refund.status = 'APPROVED'
        refund.save()
        if refund_escrow_for_job(refund.job):
            refund.status = 'REFUNDED'
            refund.save(update_fields=['status'])
        messages.success(request, f'Refund request #{refund.id} processed.')
    elif action == 'reject':
        refund.status = 'REJECTED'
        refund.save()
        messages.success(request, f'Refund request #{refund.id} rejected.')
    else:
        messages.error(request, 'Invalid action.')
    return redirect('admin_refunds')


@login_required
@never_cache
def admin_transactions(request):
    if not _is_admin(request.user):
        return redirect('dashboard')
    txns = WalletTransaction.objects.select_related('wallet', 'wallet__owner').all()[:200]
    return render(request, 'core/admin_transactions.html', {'transactions': txns})


@login_required
@never_cache
def client_refund_requests(request):
    if request.user.user_type != 'client':
        return redirect('dashboard')
    jobs = request.user.jobs.filter(status__in=['OPEN', 'IN_PROGRESS', 'SUBMITTED', 'COMPLETED']).order_by('-created_at')
    requests = RefundRequest.objects.filter(client=request.user).select_related('job')
    return render(request, 'core/client_refund_requests.html', {'jobs': jobs, 'refund_requests': requests})


@login_required
@require_POST
def create_refund_request(request):
    if request.user.user_type != 'client':
        return redirect('dashboard')
    job_id = request.POST.get('job_id')
    reason = request.POST.get('reason', '').strip()
    if not job_id or not reason:
        messages.error(request, 'Job and reason are required.')
        return redirect('client_refund_requests')
    job = get_object_or_404(request.user.jobs, id=job_id)
    existing_open = RefundRequest.objects.filter(job=job, status__in=['PENDING', 'APPROVED']).exists()
    if existing_open:
        messages.error(request, 'A refund request already exists for this job.')
        return redirect('client_refund_requests')
    RefundRequest.objects.create(job=job, client=request.user, reason=reason, status='PENDING')
    messages.success(request, 'Refund request submitted.')
    return redirect('client_refund_requests')
