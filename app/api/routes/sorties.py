from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.db.models import User, Sortie, Role
from app.schemas.sortie import SortieResponse, SortieCreate
from app.services.sortie_service import SortieService
from app.services.permission_service import PermissionService

router = APIRouter()

@router.post("", response_model=SortieResponse)
def create_sortie(sortie_in: SortieCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    PermissionService.enforce_base_scope(current_user, sortie_in.base_id)
    return SortieService.create_sortie(db, sortie_in, current_user)

@router.get("", response_model=list[SortieResponse])
def get_sorties(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == Role.ADMIN:
        return db.query(Sortie).all()
    elif current_user.role == Role.CADET:
        return db.query(Sortie).filter(Sortie.cadet_id == current_user.id).all()
    elif current_user.role == Role.INSTRUCTOR:
        return db.query(Sortie).filter(Sortie.instructor_id == current_user.id).all()
    else:
        return db.query(Sortie).filter(Sortie.base_id == current_user.base_id).all()

@router.get("/{sortie_id}", response_model=SortieResponse)
def get_sortie(sortie_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sortie = SortieService.get_sortie(db, sortie_id)
    PermissionService.can_view_sortie(current_user, sortie)
    return sortie

@router.patch("/{sortie_id}/release", response_model=SortieResponse)
def release_sortie(sortie_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sortie = SortieService.get_sortie(db, sortie_id)
    PermissionService.enforce_base_scope(current_user, sortie.base_id)
    return SortieService.release_sortie(db, sortie_id, current_user)

@router.patch("/{sortie_id}/airborne", response_model=SortieResponse)
def airborne_sortie(sortie_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sortie = SortieService.get_sortie(db, sortie_id)
    PermissionService.enforce_base_scope(current_user, sortie.base_id)
    return SortieService.airborne_sortie(db, sortie_id, current_user)

@router.patch("/{sortie_id}/landed", response_model=SortieResponse)
def landed_sortie(sortie_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sortie = SortieService.get_sortie(db, sortie_id)
    PermissionService.enforce_base_scope(current_user, sortie.base_id)
    return SortieService.landed_sortie(db, sortie_id, current_user)

@router.patch("/{sortie_id}/cancel", response_model=SortieResponse)
def cancel_sortie(sortie_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sortie = SortieService.get_sortie(db, sortie_id)
    PermissionService.enforce_base_scope(current_user, sortie.base_id)
    return SortieService.cancel_sortie(db, sortie_id, current_user)

@router.patch("/{sortie_id}/close", response_model=SortieResponse)
def close_sortie(sortie_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sortie = SortieService.get_sortie(db, sortie_id)
    PermissionService.enforce_base_scope(current_user, sortie.base_id)
    return SortieService.close_sortie(db, sortie_id, current_user)
