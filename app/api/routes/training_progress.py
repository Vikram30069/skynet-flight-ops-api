from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.db.models import User, TrainingProgress, Role, TrainingProgressStatus
from app.schemas.training_progress import TrainingProgressResponse, TrainingProgressCreate, TrainingProgressReject
from app.services.training_service import TrainingService
from app.services.permission_service import PermissionService
from app.core.errors import ForbiddenError, NotFoundError

router = APIRouter()

@router.post("", response_model=TrainingProgressResponse)
def create_training_progress(progress_in: TrainingProgressCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return TrainingService.create_or_update_progress(db, progress_in, current_user)

@router.get("/{sortie_id}", response_model=TrainingProgressResponse)
def get_training_progress(sortie_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tp = TrainingService.get_progress(db, sortie_id)
    # RBAC logic:
    if current_user.role == Role.CADET:
        if tp.cadet_id != current_user.id or tp.status != TrainingProgressStatus.APPROVED:
            raise ForbiddenError("Cadets can only view their own approved training progress")
    return tp

@router.patch("/{progress_id}/submit", response_model=TrainingProgressResponse)
def submit_training_progress(progress_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return TrainingService.submit_progress(db, progress_id, current_user)

@router.patch("/{progress_id}/approve", response_model=TrainingProgressResponse)
def approve_training_progress(progress_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return TrainingService.approve_progress(db, progress_id, current_user)

@router.patch("/{progress_id}/reject", response_model=TrainingProgressResponse)
def reject_training_progress(progress_id: str, reject_in: TrainingProgressReject, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return TrainingService.reject_progress(db, progress_id, reject_in.rejection_reason, current_user)
