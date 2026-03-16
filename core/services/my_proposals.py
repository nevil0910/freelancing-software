from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Application


@login_required
@never_cache
def my_proposals(request):
    """
    View for freelancers to see their pending (PENDING) job applications.
    Only accessible by users with 'freelancer' user_type.
    """
    if request.user.user_type != 'freelancer':
        messages.error(request, 'Only freelancers can view proposals.')
        return redirect('dashboard')

    # Get applications with status PENDING for the current freelancer
    applications = (
        Application.objects
        .filter(freelancer=request.user, status='PENDING')
        .select_related('job', 'job__client')
        .order_by('-created_at')
    )

    context = {
        'applications': applications,
    }
    return render(request, 'core/my_proposals.html', context)
