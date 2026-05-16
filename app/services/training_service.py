from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models import TrainingProgress, Sortie, SortieStatus, TrainingProgressStatus, User, Role
from app.schemas.training_progress import TrainingProgressCreate, TrainingProgressUpdate, TrainingProgressReject
from app.core.errors import NotFoundError, ForbiddenError, ConflictError, ValidationError
from app.services.audit_service import AuditService
from app.services.sortie_service import SortieService

class TrainingService:
    @staticmethod
    def get_progress(db: Session, sortie_id: str) -> TrainingProgress:
        tp = db.query(TrainingProgress).filter(TrainingProgress.sortie_id == sortie_id).first()
        if not tp:
            raise NotFoundError("Training progress not found")
        return tp

    @staticmethod
    def create_or_update_progress(db: Session, progress_in: TrainingProgressCreate, current_user: User) -> TrainingProgress:
        if current_user.role not in [Role.INSTRUCTOR, Role.ADMIN]:
            raise ForbiddenError("Only instructors can submit training progress")
            
        sortie = SortieService.get_sortie(db, progress_in.sortie_id)
        if current_user.role == Role.INSTRUCTOR and sortie.instructor_id != current_user.id:
            raise ForbiddenError("Only assigned instructor can submit training progress")
            
        tp = db.query(TrainingProgress).filter(TrainingProgress.sortie_id == progress_in.sortie_id).first()
        
        if tp:
            if tp.status in [TrainingProgressStatus.SUBMITTED, TrainingProgressStatus.APPROVED]:
                raise ConflictError("Cannot edit progress that is already submitted or approved")
            tp.maneuver_score = progress_in.maneuver_score
            tp.communication_score = progress_in.communication_score
            tp.situational_awareness_score = progress_in.situational_awareness_score
            tp.remarks = progress_in.remarks
            tp.status = TrainingProgressStatus.DRAFT
        else:
            tp = TrainingProgress(
                sortie_id=sortie.id,
                cadet_id=sortie.cadet_id,
                instructor_id=sortie.instructor_id,
                lesson_type=progress_in.lesson_type,
                maneuver_score=progress_in.maneuver_score,
                communication_score=progress_in.communication_score,
                situational_awareness_score=progress_in.situational_awareness_score,
                remarks=progress_in.remarks,
                status=TrainingProgressStatus.DRAFT
            )
            db.add(tp)
            
        db.commit()
        db.refresh(tp)
        return tp

    @staticmethod
    def submit_progress(db: Session, progress_id: str, current_user: User) -> TrainingProgress:
        tp = db.query(TrainingProgress).filter(TrainingProgress.id == progress_id).first()
        if not tp:
            raise NotFoundError("Training progress not found")
            
        if current_user.role not in [Role.INSTRUCTOR, Role.ADMIN]:
            raise ForbiddenError()
            
        if current_user.role == Role.INSTRUCTOR and tp.instructor_id != current_user.id:
            raise ForbiddenError()
            
        if not tp.remarks:
            raise ValidationError("Remarks cannot be empty during submission", field="remarks")
            
        tp.status = TrainingProgressStatus.SUBMITTED
        tp.submitted_at = datetime.utcnow()
        db.commit()
        db.refresh(tp)
        
        # Advance sortie state
        sortie = SortieService.get_sortie(db, tp.sortie_id)
        SortieService._transition(db, sortie, SortieStatus.TRAINING_SUBMITTED, current_user)
        
        AuditService.log_action(db, current_user, "TRAINING_SUBMITTED", "training_progress", tp.id)
        return tp

    @staticmethod
    def approve_progress(db: Session, progress_id: str, current_user: User) -> TrainingProgress:
        if current_user.role not in [Role.CFI, Role.ADMIN]:
            raise ForbiddenError("Only CFI can approve training progress")
            
        tp = db.query(TrainingProgress).filter(TrainingProgress.id == progress_id).first()
        if not tp:
            raise NotFoundError()
            
        if tp.status != TrainingProgressStatus.SUBMITTED:
            raise ConflictError("Only submitted progress can be approved")
            
        tp.status = TrainingProgressStatus.APPROVED
        tp.approved_by = current_user.id
        tp.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(tp)
        
        # Advance sortie state
        sortie = SortieService.get_sortie(db, tp.sortie_id)
        SortieService._transition(db, sortie, SortieStatus.TRAINING_APPROVED, current_user)
        
        AuditService.log_action(db, current_user, "TRAINING_APPROVED", "training_progress", tp.id)
        return tp

    @staticmethod
    def reject_progress(db: Session, progress_id: str, reason: str, current_user: User) -> TrainingProgress:
        if current_user.role not in [Role.CFI, Role.ADMIN]:
            raise ForbiddenError()
            
        tp = db.query(TrainingProgress).filter(TrainingProgress.id == progress_id).first()
        if not tp:
            raise NotFoundError()
            
        tp.status = TrainingProgressStatus.REJECTED
        tp.rejection_reason = reason
        db.commit()
        db.refresh(tp)
        
        AuditService.log_action(db, current_user, "TRAINING_REJECTED", "training_progress", tp.id, new_value=reason)
        return tp
