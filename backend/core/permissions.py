from rest_framework.permissions import BasePermission
from core.constants import UserRoles

class IsSuperAdmin(BasePermission):
    """
    Allows access only to Super Admins (Global System Admins).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == UserRoles.SUPER_ADMIN or getattr(request.user, 'is_superadmin', False) or request.user.is_superuser)
        )


class IsAdminUser(BasePermission):
    """
    Allows access to Super Admins or Company Admin Users.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == UserRoles.SUPER_ADMIN or getattr(request.user, 'is_superadmin', False) or request.user.is_superuser:
            return True
        return bool(
            (request.user.role == UserRoles.ADMIN_USER or getattr(request.user, 'is_company_admin', False)) and
            request.user.company is not None
        )


# Alias for backward compatibility
IsCompanyAdmin = IsAdminUser


class IsCompanyUser(BasePermission):
    """
    Allows access to any user associated with a company or Super Admin.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == UserRoles.SUPER_ADMIN or getattr(request.user, 'is_superadmin', False) or request.user.is_superuser:
            return True
        return bool(request.user.company is not None)


class HasModulePrivilege(BasePermission):
    """
    Dynamic permission to check module privileges.
    Super Admins and Admin Users have full access.
    Company Users (Employees) are checked against their assigned Role Privileges.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Super Admin and Admin User have full access
        if request.user.role in [UserRoles.SUPER_ADMIN, UserRoles.ADMIN_USER] or getattr(request.user, 'is_superadmin', False) or getattr(request.user, 'is_company_admin', False) or request.user.is_superuser:
            return True

        # Check role and privileges for Company Users / Employees
        role = getattr(request.user, 'custom_role', None)
        if not role:
            return False

        module = getattr(view, 'required_module', None)
        if not module:
            return True

        action_map = {
            'GET': 'can_read',
            'HEAD': 'can_read',
            'OPTIONS': 'can_read',
            'POST': 'can_create',
            'PUT': 'can_update',
            'PATCH': 'can_update',
            'DELETE': 'can_delete',
        }
        required_action = action_map.get(request.method, 'can_read')

        privilege = role.privileges.filter(module=module, is_deleted=False).first()
        if not privilege:
            return False

        return getattr(privilege, required_action, False)
