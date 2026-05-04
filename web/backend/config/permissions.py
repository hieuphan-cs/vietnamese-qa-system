from rest_framework import permissions

class IsAdminOrTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Cho phép các method GET, HEAD, OPTIONS
        if request.method in permissions.SAFE_METHODS:
            return True

        # Lấy role, lỡ có lỗi thì mặc định là STUDENT, và ép tất cả thành IN HOA
        user_role = getattr(request.user, 'role', 'STUDENT').upper()
        
        return user_role in ['ADMIN', 'TEACHER']


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        user_role = getattr(request.user, 'role', 'STUDENT').upper()
        
        return user_role == 'ADMIN'