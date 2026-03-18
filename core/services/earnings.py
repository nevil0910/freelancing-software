from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db.models import Sum
from ..models import Earning


@login_required
@never_cache
def earnings_view(request):
    """
    Earnings page for freelancers.
    Shows a table of all earnings sorted by newest, with total on top.
    """
    if request.user.user_type != 'freelancer':
        from django.shortcuts import redirect
        return redirect('dashboard')

    earnings_list = Earning.objects.filter(
        freelancer=request.user
    ).select_related('job').order_by('-earned_at')

    total_earnings = earnings_list.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'earnings': earnings_list,
        'total_earnings': total_earnings,
    }
    return render(request, 'core/earnings.html', context)
