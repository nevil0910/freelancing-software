from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from ..models import Wallet, WalletTransaction, Escrow, Earning


def get_platform_wallet():
    wallet, _ = Wallet.objects.get_or_create(wallet_type='PLATFORM', defaults={'balance': Decimal('0.00')})
    return wallet


def get_user_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(owner=user, defaults={'wallet_type': 'USER', 'balance': Decimal('0.00')})
    return wallet


@transaction.atomic
def fund_escrow_for_job(job):
    if hasattr(job, 'escrow'):
        return job.escrow
    escrow = Escrow.objects.create(
        job=job,
        client=job.client,
        amount=job.budget,
        commission_rate=Decimal('5.00'),
    )
    platform_wallet = get_platform_wallet()
    platform_wallet.balance = (platform_wallet.balance or Decimal('0.00')) + job.budget
    platform_wallet.save(update_fields=['balance', 'updated_at'])
    WalletTransaction.objects.create(
        wallet=platform_wallet,
        direction='CREDIT',
        amount=job.budget,
        reference_type='ESCROW_FUND',
        reference_id=str(job.id),
        note=f'Escrow funded for job #{job.id}',
    )
    return escrow


@transaction.atomic
def release_escrow_for_job(job, freelancer):
    escrow = getattr(job, 'escrow', None)
    if not escrow or escrow.status != 'FUNDED':
        return False
    platform_wallet = get_platform_wallet()
    freelancer_wallet = get_user_wallet(freelancer)
    commission = (escrow.amount * escrow.commission_rate) / Decimal('100.00')
    freelancer_share = escrow.amount - commission
    escrow.commission_amount = commission
    escrow.freelancer_amount = freelancer_share
    escrow.status = 'RELEASED'
    escrow.released_at = timezone.now()
    escrow.save()

    platform_wallet.balance = platform_wallet.balance - freelancer_share
    platform_wallet.save(update_fields=['balance', 'updated_at'])
    WalletTransaction.objects.create(
        wallet=platform_wallet,
        direction='DEBIT',
        amount=freelancer_share,
        reference_type='ESCROW_RELEASE',
        reference_id=str(job.id),
        note=f'Release to freelancer for job #{job.id}',
    )

    freelancer_wallet.balance = freelancer_wallet.balance + freelancer_share
    freelancer_wallet.save(update_fields=['balance', 'updated_at'])
    WalletTransaction.objects.create(
        wallet=freelancer_wallet,
        direction='CREDIT',
        amount=freelancer_share,
        reference_type='EARNING',
        reference_id=str(job.id),
        note=f'Job completion payout #{job.id}',
    )
    Earning.objects.get_or_create(
        freelancer=freelancer,
        job=job,
        defaults={'amount': freelancer_share}
    )
    return True


@transaction.atomic
def refund_escrow_for_job(job):
    escrow = getattr(job, 'escrow', None)
    if not escrow or escrow.status != 'FUNDED':
        return False
    platform_wallet = get_platform_wallet()
    client_wallet = get_user_wallet(job.client)
    escrow.status = 'REFUNDED'
    escrow.refunded_at = timezone.now()
    escrow.save(update_fields=['status', 'refunded_at'])

    platform_wallet.balance = platform_wallet.balance - escrow.amount
    platform_wallet.save(update_fields=['balance', 'updated_at'])
    WalletTransaction.objects.create(
        wallet=platform_wallet,
        direction='DEBIT',
        amount=escrow.amount,
        reference_type='REFUND',
        reference_id=str(job.id),
        note=f'Refund for job #{job.id}',
    )

    client_wallet.balance = client_wallet.balance + escrow.amount
    client_wallet.save(update_fields=['balance', 'updated_at'])
    WalletTransaction.objects.create(
        wallet=client_wallet,
        direction='CREDIT',
        amount=escrow.amount,
        reference_type='REFUND',
        reference_id=str(job.id),
        note=f'Refund received for job #{job.id}',
    )
    return True
