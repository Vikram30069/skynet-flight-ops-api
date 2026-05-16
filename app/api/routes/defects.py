from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.db.models import User, Defect, Role
from app.schemas.defect import DefectResponse, DefectCreate
from app.services.defect_service import DefectService
from app.services.permission_service import PermissionService

router = APIRouter()

@router.post("", response_model=DefectResponse)
def create_defect(defect_in: DefectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return DefectService.create_defect(db, defect_in, current_user)

@router.get("", response_model=list[DefectResponse])
def get_defects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == Role.ADMIN:
        return db.query(Defect).all()
    else:
        # A simpler query, could be base-scoped by joining with aircraft
        # For simplicity of this assessment, assuming maintenance officer can see all defects at their base.
        from app.db.models import Aircraft
        return db.query(Defect).join(Aircraft).filter(Aircraft.base_id == current_user.base_id).all()

@router.get("/{defect_id}", response_model=DefectResponse)
def get_defect(defect_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    defect = DefectService.get_defect(db, defect_id)
    return defect

@router.patch("/{defect_id}/resolve", response_model=DefectResponse)
def resolve_defect(defect_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return DefectService.resolve_defect(db, defect_id, current_user)

@router.patch("/{defect_id}/defer", response_model=DefectResponse)
def defer_defect(defect_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return DefectService.defer_defect(db, defect_id, current_user)
