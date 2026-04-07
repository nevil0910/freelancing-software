from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse


class BlockedUserMiddleware:
    """Force-blocked accounts out of the app except login/logout endpoints."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and getattr(request.user, 'is_blocked', False):
            allowed = {
                reverse('logout'),
                reverse('login'),
            }
            if request.path not in allowed:
                logout(request)
                messages.error(request, 'Your account is blocked. Contact support.')
                return redirect('login')
        return self.get_response(request)
