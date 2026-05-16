from sqlalchemy.orm import Session
from app.db.models import Aircraft, AircraftStatus, User, Defect, DefectStatus, DefectSeverity
from app.core.errors import NotFoundError, InvalidStateTransitionError, ConflictError
from app.services.audit_service import AuditService

class AircraftService:
    @staticmethod
    def get_aircraft(db: Session, aircraft_id: str) -> Aircraft:
        aircraft = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
        if not aircraft:
            raise NotFoundError("Aircraft not found")
        return aircraft

    @staticmethod
    def change_status(db: Session, aircraft: Aircraft, new_status: AircraftStatus, current_user: User, reason: str = None):
        old_status = aircraft.status
        if old_status == new_status:
            return aircraft
        
        aircraft.status = new_status
        db.commit()
        db.refresh(aircraft)

        AuditService.log_action(
            db=db,
            actor=current_user,
            action=f"AIRCRAFT_{new_status.value}",
            entity_type="aircraft",
            entity_id=aircraft.id,
            old_value=old_status.value,
            new_value=new_status.value,
            reason=reason
        )
        return aircraft

    @staticmethod
    def ground_aircraft(db: Session, aircraft_id: str, current_user: User, reason: str = None) -> Aircraft:
        aircraft = AircraftService.get_aircraft(db, aircraft_id)
        if aircraft.status == AircraftStatus.GROUNDED:
            return aircraft
        
        return AircraftService.change_status(db, aircraft, AircraftStatus.GROUNDED, current_user, reason)

    @staticmethod
    def mark_ready(db: Session, aircraft_id: str, current_user: User) -> Aircraft:
        aircraft = AircraftService.get_aircraft(db, aircraft_id)
        
        # Check for open critical/high defects
        open_critical_defects = db.query(Defect).filter(
            Defect.aircraft_id == aircraft_id,
            Defect.status == DefectStatus.OPEN,
            Defect.severity.in_([DefectSeverity.HIGH, DefectSeverity.CRITICAL])
        ).count()

        if open_critical_defects > 0:
            raise ConflictError("Cannot mark aircraft ready: open critical/high defects exist.")

        return AircraftService.change_status(db, aircraft, AircraftStatus.READY, current_user)
