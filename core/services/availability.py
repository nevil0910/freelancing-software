from django.http import JsonResponse
from ..models import CustomUser


def check_username_availability(request):
    """API endpoint to check if username is available"""
    if request.method != 'POST':
        return JsonResponse({'available': False, 'error': 'Invalid request method'})

    username = request.POST.get('username', '').strip()

    if not username:
        return JsonResponse({'available': False, 'error': 'Username is required'})

    # Check if username exists in CustomUser
    user_exists = CustomUser.objects.filter(username=username).exists()

    available = not user_exists

    return JsonResponse({'available': available})


def check_email_availability(request):
    """API endpoint to check if email is available"""
    if request.method != 'POST':
        return JsonResponse({'available': False, 'error': 'Invalid request method'})

    email = request.POST.get('email', '').strip()

    if not email:
        return JsonResponse({'available': False, 'error': 'Email is required'})

    # Check if email exists in CustomUser
    user_exists = CustomUser.objects.filter(email=email).exists()

    available = not user_exists

    return JsonResponse({'available': available})
