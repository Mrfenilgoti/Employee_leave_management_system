from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    """
    Custom permission to allow access only to Manager or Main Manager roles.
    """
    def has_permission(self, request, view):
        return bool(
            request.user 
            and request.user.is_authenticated 
            and (request.user.is_manager or request.user.is_main_manager)
        )