from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is a staff member or superuser.
    Raises PermissionDenied (403) if the user is not an admin, instead of redirecting to login loop.
    """
    def check_perms(user):
        if not user.is_authenticated:
            return False
        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied
        return True
        
    return user_passes_test(check_perms, login_url='/account/login/')(view_func)
