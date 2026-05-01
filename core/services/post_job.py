from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..forms import JobForm


@login_required
@never_cache
def post_job(request):
    """
    View for clients to post a new job.
    Only accessible by users with 'client' user_type.
    """
    # Check if user is a client
    if request.user.user_type != 'client':
        messages.error(request, 'Only clients can post jobs.')
        return redirect('dashboard')

    if request.method == 'POST':
        messages.error(request, 'Please complete the payment checkout to post your job.')
        return redirect('post_job')

    form = JobForm()

    return render(request, 'core/post_job.html', {'form': form})
