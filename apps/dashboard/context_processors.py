from .console_permissions import has_console_access


def console_access(request):
    return {'console_access': has_console_access(getattr(request, 'user', None))}
