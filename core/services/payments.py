from decimal import Decimal
from uuid import uuid4

import razorpay
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.cache import never_cache
from razorpay.errors import SignatureVerificationError

from ..forms import JobForm
from .escrow import fund_escrow_for_job


def _get_razorpay_client():
    if not settings.RAZORPAY_ENABLED:
        raise ValueError('Razorpay is not enabled.')
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise ValueError('Razorpay API keys are not configured.')
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def _serialize_job_form_data(cleaned_data):
    return {
        'title': cleaned_data['title'],
        'tagline': cleaned_data['tagline'],
        'description': cleaned_data['description'],
        'category': cleaned_data['category'],
        'budget': str(cleaned_data['budget']),
        'deadline': cleaned_data['deadline'].isoformat(),
        'required_freelancers': str(cleaned_data['required_freelancers']),
    }


@login_required
@never_cache
def create_post_job_order(request):
    if request.user.user_type != 'client':
        return JsonResponse({'success': False, 'error': 'Only clients can post jobs.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    form = JobForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    try:
        client = _get_razorpay_client()
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

    amount = form.cleaned_data['budget']
    amount_paise = int((Decimal(amount) * 100).quantize(Decimal('1')))
    order_payload = {
        'amount': amount_paise,
        'currency': settings.RAZORPAY_CURRENCY,
        'receipt': f'job_{request.user.id}_{uuid4().hex[:16]}',
        'payment_capture': 1,
    }

    try:
        order = client.order.create(data=order_payload)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Failed to create payment order.'}, status=500)

    pending_orders = request.session.get('pending_job_orders', {})
    pending_orders[order['id']] = {
        'form_data': _serialize_job_form_data(form.cleaned_data),
        'amount': str(amount),
    }
    request.session['pending_job_orders'] = pending_orders
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'key': settings.RAZORPAY_KEY_ID,
        'order_id': order['id'],
        'amount': order['amount'],
        'currency': order['currency'],
        'name': settings.APP_NAME,
        'description': 'Job posting escrow payment',
        'prefill': {
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        },
    })


@login_required
@never_cache
def verify_post_job_payment(request):
    if request.user.user_type != 'client':
        return JsonResponse({'success': False, 'error': 'Only clients can post jobs.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    razorpay_order_id = request.POST.get('razorpay_order_id', '').strip()
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '').strip()
    razorpay_signature = request.POST.get('razorpay_signature', '').strip()

    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        return JsonResponse({'success': False, 'error': 'Missing payment verification data.'}, status=400)

    pending_orders = request.session.get('pending_job_orders', {})
    order_data = pending_orders.get(razorpay_order_id)
    if not order_data:
        return JsonResponse({'success': False, 'error': 'No pending job data found for this payment order.'}, status=400)

    try:
        client = _get_razorpay_client()
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })
    except SignatureVerificationError:
        return JsonResponse({'success': False, 'error': 'Payment signature verification failed.'}, status=400)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Unable to verify payment.'}, status=500)

    form = JobForm(order_data['form_data'])
    if not form.is_valid():
        return JsonResponse({'success': False, 'error': 'Job details are no longer valid. Please submit again.'}, status=400)

    with transaction.atomic():
        job = form.save(commit=False)
        job.client = request.user
        job.status = 'OPEN'
        job.save()
        fund_escrow_for_job(job)

    pending_orders.pop(razorpay_order_id, None)
    request.session['pending_job_orders'] = pending_orders
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'message': 'Payment verified and job posted successfully.',
        'redirect_url': reverse('my_jobs'),
    })