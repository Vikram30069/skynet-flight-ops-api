from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models import Sortie, SortieStatus, User, Role, Aircraft, AircraftStatus, Defect, DefectStatus, DefectSeverity
from app.schemas.sortie import SortieCreate
from app.core.errors import NotFoundError, InvalidStateTransitionError, ConflictError, ForbiddenError
from app.services.audit_service import AuditService
from app.services.aircraft_service import AircraftService

class SortieService:
    VALID_TRANSITIONS = {
        SortieStatus.SCHEDULED: [SortieStatus.RELEASED, SortieStatus.CANCELLED],
        SortieStatus.RELEASED: [SortieStatus.AIRBORNE, SortieStatus.CANCELLED],
        SortieStatus.AIRBORNE: [SortieStatus.LANDED],
        SortieStatus.LANDED: [SortieStatus.TRAINING_SUBMITTED, SortieStatus.CLOSED], # Can close directly if no training needed? No, rules say training approval needed. Wait, wait, rules say:
        # LANDED -> TRAINING_SUBMITTED
        # Wait, if defect, aircraft grounded, sortie cannot close until recovery. But state stays LANDED or AIRCRAFT_GROUNDED? Prompt: "Sortie cannot close until recovery decision or maintenance resolution is added".
        # Let's enforce standard: LANDED -> TRAINING_SUBMITTED -> TRAINING_APPROVED -> CLOSED.
        SortieStatus.TRAINING_SUBMITTED: [SortieStatus.TRAINING_APPROVED],
        SortieStatus.TRAINING_APPROVED: [SortieStatus.CLOSED],
        SortieStatus.CANCELLED: [],
        SortieStatus.CLOSED: [],
        SortieStatus.AIRCRAFT_GROUNDED: [SortieStatus.RECOVERY_REQUIRED, SortieStatus.CLOSED], # Simplified for exception handling
        SortieStatus.RECOVERY_REQUIRED: [SortieStatus.CLOSED]
    }

    @staticmethod
    def get_sortie(db: Session, sortie_id: str) -> Sortie:
        sortie = db.query(Sortie).filter(Sortie.id == sortie_id).first()
        if not sortie:
            raise NotFoundError("Sortie not found")
        return sortie

    @staticmethod
    def create_sortie(db: Session, sortie_in: SortieCreate, current_user: User) -> Sortie:
        if current_user.role not in [Role.DISPATCHER, Role.ADMIN]:
            raise ForbiddenError("Only dispatchers can create sorties")

        aircraft = AircraftService.get_aircraft(db, sortie_in.aircraft_id)
        if aircraft.status == AircraftStatus.GROUNDED:
            raise ConflictError("Grounded aircraft cannot be assigned to a new sortie")

        # Overlap check
        overlapping = db.query(Sortie).filter(
            Sortie.aircraft_id == sortie_in.aircraft_id,
            Sortie.status.in_([SortieStatus.SCHEDULED, SortieStatus.RELEASED, SortieStatus.AIRBORNE]),
            Sortie.scheduled_start < sortie_in.scheduled_end,
            Sortie.scheduled_end > sortie_in.scheduled_start
        ).first()

        if overlapping:
            raise ConflictError("Aircraft is already assigned to an overlapping sortie")

        sortie = Sortie(
            **sortie_in.model_dump(),
            status=SortieStatus.SCHEDULED
        )
        db.add(sortie)
        db.commit()
        db.refresh(sortie)

        AircraftService.change_status(db, aircraft, AircraftStatus.SCHEDULED, current_user)

        AuditService.log_action(db, current_user, "SORTIE_CREATED", "sortie", sortie.id)
        return sortie

    @staticmethod
    def _transition(db: Session, sortie: Sortie, new_status: SortieStatus, current_user: User):
        if new_status not in SortieService.VALID_TRANSITIONS.get(sortie.status, []):
            raise InvalidStateTransitionError(f"Cannot move sortie from {sortie.status.value} to {new_status.value}")
        
        old_status = sortie.status
        sortie.status = new_status
        db.commit()
        db.refresh(sortie)

        AuditService.log_action(
            db, current_user, f"SORTIE_{new_status.value}", "sortie", sortie.id,
            old_value=old_status.value, new_value=new_status.value
        )
        return sortie

    @staticmethod
    def release_sortie(db: Session, sortie_id: str, current_user: User) -> Sortie:
        if current_user.role not in [Role.DISPATCHER, Role.ADMIN]:
            raise ForbiddenError()
            
        sortie = SortieService.get_sortie(db, sortie_id)
        
        aircraft = AircraftService.get_aircraft(db, sortie.aircraft_id)
        if aircraft.status == AircraftStatus.GROUNDED:
            raise ConflictError("Grounded aircraft cannot be released")

        return SortieService._transition(db, sortie, SortieStatus.RELEASED, current_user)

    @staticmethod
    def airborne_sortie(db: Session, sortie_id: str, current_user: User) -> Sortie:
        if current_user.role not in [Role.DISPATCHER, Role.ADMIN]:
            raise ForbiddenError()
            
        sortie = SortieService.get_sortie(db, sortie_id)
        sortie.actual_start = datetime.utcnow()
        SortieService._transition(db, sortie, SortieStatus.AIRBORNE, current_user)
        
        aircraft = AircraftService.get_aircraft(db, sortie.aircraft_id)
        AircraftService.change_status(db, aircraft, AircraftStatus.AIRBORNE, current_user)
        
        return sortie

    @staticmethod
    def landed_sortie(db: Session, sortie_id: str, current_user: User) -> Sortie:
        if current_user.role not in [Role.DISPATCHER, Role.ADMIN]:
            raise ForbiddenError()
            
        sortie = SortieService.get_sortie(db, sortie_id)
        sortie.actual_end = datetime.utcnow()
        SortieService._transition(db, sortie, SortieStatus.LANDED, current_user)
        
        aircraft = AircraftService.get_aircraft(db, sortie.aircraft_id)
        AircraftService.change_status(db, aircraft, AircraftStatus.LANDED, current_user)
        
        return sortie

    @staticmethod
    def cancel_sortie(db: Session, sortie_id: str, current_user: User) -> Sortie:
        if current_user.role not in [Role.DISPATCHER, Role.ADMIN]:
            raise ForbiddenError()
            
        sortie = SortieService.get_sortie(db, sortie_id)
        SortieService._transition(db, sortie, SortieStatus.CANCELLED, current_user)
        
        aircraft = AircraftService.get_aircraft(db, sortie.aircraft_id)
        if aircraft.status in [AircraftStatus.SCHEDULED, AircraftStatus.READY]:
             AircraftService.mark_ready(db, aircraft.id, current_user) # Reset to ready if it was scheduled

        return sortie

    @staticmethod
    def close_sortie(db: Session, sortie_id: str, current_user: User) -> Sortie:
        if current_user.role not in [Role.DISPATCHER, Role.ADMIN]:
            raise ForbiddenError()
            
        sortie = SortieService.get_sortie(db, sortie_id)
        
        if sortie.status != SortieStatus.TRAINING_APPROVED:
            # Exception workflow: if aircraft grounded, we might close if defects handled
            aircraft = AircraftService.get_aircraft(db, sortie.aircraft_id)
            if aircraft.status == AircraftStatus.GROUNDED:
                raise ConflictError("A sortie with grounded aircraft must not be closed unless defect is resolved/deferred")
            raise InvalidStateTransitionError(f"Cannot close sortie. Training must be approved first.")
            
        SortieService._transition(db, sortie, SortieStatus.CLOSED, current_user)
        
        # Aircraft becomes ready if it landed safely and is not grounded
        aircraft = AircraftService.get_aircraft(db, sortie.aircraft_id)
        if aircraft.status == AircraftStatus.LANDED:
            AircraftService.mark_ready(db, aircraft.id, current_user)
            
        return sortie
