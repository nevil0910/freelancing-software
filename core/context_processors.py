from django.conf import settings


def app_name(request):
    """
    Context processor to make APP_NAME available in all templates.
    """
    return {
        'APP_NAME': settings.APP_NAME
    }
