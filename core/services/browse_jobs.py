from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Job


@login_required
@never_cache
def browse_jobs(request):
    """
    View for freelancers to browse and search available jobs.
    Only accessible by users with 'freelancer' user_type.
    Supports filtering by category, search by client, and sorting.
    """
    # Check if user is a freelancer
    if request.user.user_type != 'freelancer':
        messages.error(request, 'Only freelancers can browse jobs.')
        return redirect('dashboard')

    # Get all OPEN jobs
    jobs = Job.objects.filter(status='OPEN').select_related('client')

    # Get filter parameters from POST (form uses method="post")
    category = request.POST.get('category', '')
    search = request.POST.get('search', '')
    sort = request.POST.get('sort', 'newest')

    # Apply category filter
    if category:
        jobs = jobs.filter(category=category)

    # Apply search filter (client username)
    if search:
        jobs = jobs.filter(client__username__icontains=search)

    # Apply sorting
    if sort == 'newest':
        jobs = jobs.order_by('-created_at')
    elif sort == 'budget_low':
        jobs = jobs.order_by('budget')
    elif sort == 'budget_high':
        jobs = jobs.order_by('-budget')
    elif sort == 'deadline_earliest':
        jobs = jobs.order_by('deadline')
    elif sort == 'deadline_latest':
        jobs = jobs.order_by('-deadline')
    else:
        jobs = jobs.order_by('-created_at')

    # Get category choices for the filter dropdown
    categories = Job.CATEGORY_CHOICES

    context = {
        'jobs': jobs,
        'categories': categories,
        'selected_category': category,
        'search_query': search,
        'selected_sort': sort,
    }

    return render(request, 'core/browse_jobs.html', context)
