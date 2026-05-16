from app.db.models import User, Role
from app.core.errors import ForbiddenError

class PermissionService:
    @staticmethod
    def require_role(user: User, allowed_roles: list[Role]):
        if user.role not in allowed_roles:
            raise ForbiddenError()

    @staticmethod
    def enforce_base_scope(user: User, entity_base_id: str):
        if user.role == Role.ADMIN:
            return
        if user.base_id != entity_base_id:
            raise ForbiddenError("Base mismatch. You cannot access records outside your assigned base.")

    @staticmethod
    def can_view_sortie(user: User, sortie):
        if user.role == Role.ADMIN:
            return True
        if user.role == Role.CADET and sortie.cadet_id != user.id:
            raise ForbiddenError("Cadet can only view their own sortie")
        if user.role == Role.INSTRUCTOR and sortie.instructor_id != user.id:
            # Let's assume instructors can only view assigned sorties unless it's just viewing all base sorties?
            # Instructions: "Instructor can view assigned sorties and assigned cadet progress."
            raise ForbiddenError("Instructor can only view assigned sorties")
        
        # Dispatcher, CFI, Maintenance can view all within base
        if user.role != Role.CADET and user.role != Role.INSTRUCTOR:
            PermissionService.enforce_base_scope(user, sortie.base_id)
        
        return True
