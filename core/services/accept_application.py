from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from ..models import Application


@login_required
@never_cache
def accept_application(request, application_id):
    """
    Client accepts a freelancer application.
    Returns JSON for AJAX handling.
    """
    if request.user.user_type != 'client':
        return JsonResponse({'success': False, 'error': 'Unauthorized.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    application = get_object_or_404(Application, id=application_id, job__client=request.user)
    application.status = 'ACCEPTED'
    application.save()
    return JsonResponse({'success': True, 'status': 'ACCEPTED', 'message': 'Application accepted.'})
