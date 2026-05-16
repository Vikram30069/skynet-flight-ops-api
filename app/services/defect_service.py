from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models import Defect, User, DefectStatus, DefectSeverity, Role
from app.schemas.defect import DefectCreate
from app.core.errors import NotFoundError, ForbiddenError
from app.services.audit_service import AuditService
from app.services.aircraft_service import AircraftService

class DefectService:
    @staticmethod
    def get_defect(db: Session, defect_id: str) -> Defect:
        defect = db.query(Defect).filter(Defect.id == defect_id).first()
        if not defect:
            raise NotFoundError("Defect not found")
        return defect

    @staticmethod
    def create_defect(db: Session, defect_in: DefectCreate, current_user: User) -> Defect:
        defect = Defect(
            aircraft_id=defect_in.aircraft_id,
            sortie_id=defect_in.sortie_id,
            reported_by=current_user.id,
            severity=defect_in.severity,
            description=defect_in.description,
            status=DefectStatus.OPEN
        )
        db.add(defect)
        db.commit()
        db.refresh(defect)

        AuditService.log_action(
            db=db,
            actor=current_user,
            action="DEFECT_CREATED",
            entity_type="defect",
            entity_id=defect.id,
            new_value={"severity": defect.severity.value, "description": defect.description}
        )

        # Critical defect grounds aircraft immediately
        if defect.severity == DefectSeverity.CRITICAL:
            AircraftService.ground_aircraft(
                db=db, 
                aircraft_id=defect.aircraft_id, 
                current_user=current_user, 
                reason="Auto-grounded due to CRITICAL defect"
            )

        return defect

    @staticmethod
    def resolve_defect(db: Session, defect_id: str, current_user: User) -> Defect:
        if current_user.role not in [Role.MAINTENANCE_OFFICER, Role.ADMIN]:
            raise ForbiddenError("Only maintenance or admin can resolve defects.")
            
        defect = DefectService.get_defect(db, defect_id)
        if defect.status == DefectStatus.RESOLVED:
            return defect
            
        defect.status = DefectStatus.RESOLVED
        defect.resolved_by = current_user.id
        defect.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(defect)

        AuditService.log_action(
            db=db,
            actor=current_user,
            action="DEFECT_RESOLVED",
            entity_type="defect",
            entity_id=defect.id,
            old_value=DefectStatus.OPEN.value,
            new_value=DefectStatus.RESOLVED.value
        )
        return defect

    @staticmethod
    def defer_defect(db: Session, defect_id: str, current_user: User) -> Defect:
        if current_user.role not in [Role.MAINTENANCE_OFFICER, Role.ADMIN]:
            raise ForbiddenError("Only maintenance or admin can defer defects.")
            
        defect = DefectService.get_defect(db, defect_id)
        if defect.status == DefectStatus.DEFERRED:
            return defect
            
        defect.status = DefectStatus.DEFERRED
        defect.resolved_by = current_user.id # Treat defers as handled by someone
        defect.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(defect)

        AuditService.log_action(
            db=db,
            actor=current_user,
            action="DEFECT_DEFERRED",
            entity_type="defect",
            entity_id=defect.id,
            old_value=DefectStatus.OPEN.value,
            new_value=DefectStatus.DEFERRED.value
        )
        return defect
