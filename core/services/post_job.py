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
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.client = request.user
            job.status = 'OPEN'
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('my_jobs')
        else:
            # Form has validation errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = JobForm()

    return render(request, 'core/post_job.html', {'form': form})
