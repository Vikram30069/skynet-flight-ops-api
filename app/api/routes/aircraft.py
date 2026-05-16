from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.db.models import User, Aircraft, Role
from app.schemas.aircraft import AircraftResponse, AircraftCreate
from app.services.aircraft_service import AircraftService
from app.services.permission_service import PermissionService

router = APIRouter()

@router.post("", response_model=AircraftResponse)
def create_aircraft(aircraft_in: AircraftCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    PermissionService.require_role(current_user, [Role.ADMIN])
    aircraft = Aircraft(**aircraft_in.model_dump())
    db.add(aircraft)
    db.commit()
    db.refresh(aircraft)
    return aircraft

@router.get("", response_model=list[AircraftResponse])
def get_aircrafts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == Role.ADMIN:
        return db.query(Aircraft).all()
    else:
        return db.query(Aircraft).filter(Aircraft.base_id == current_user.base_id).all()

@router.get("/{aircraft_id}", response_model=AircraftResponse)
def get_aircraft(aircraft_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    aircraft = AircraftService.get_aircraft(db, aircraft_id)
    PermissionService.enforce_base_scope(current_user, aircraft.base_id)
    return aircraft

@router.patch("/{aircraft_id}/ground", response_model=AircraftResponse)
def ground_aircraft(aircraft_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    PermissionService.require_role(current_user, [Role.ADMIN, Role.MAINTENANCE_OFFICER, Role.DISPATCHER])
    aircraft = AircraftService.get_aircraft(db, aircraft_id)
    PermissionService.enforce_base_scope(current_user, aircraft.base_id)
    return AircraftService.ground_aircraft(db, aircraft_id, current_user, reason="Manual grounding")

@router.patch("/{aircraft_id}/ready", response_model=AircraftResponse)
def ready_aircraft(aircraft_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    PermissionService.require_role(current_user, [Role.ADMIN, Role.MAINTENANCE_OFFICER])
    aircraft = AircraftService.get_aircraft(db, aircraft_id)
    PermissionService.enforce_base_scope(current_user, aircraft.base_id)
    return AircraftService.mark_ready(db, aircraft_id, current_user)
