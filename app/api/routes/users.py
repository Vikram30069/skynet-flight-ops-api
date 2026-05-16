from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.db.models import User, BaseEntity, Role
from app.schemas.user import UserResponse
from app.schemas.base import BaseEntityResponse
from app.core.errors import NotFoundError
from app.services.permission_service import PermissionService

router_users = APIRouter()
router_bases = APIRouter()

@router_users.get("", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == Role.ADMIN:
        return db.query(User).all()
    else:
        return db.query(User).filter(User.base_id == current_user.base_id).all()

@router_users.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found")
    PermissionService.enforce_base_scope(current_user, user.base_id)
    return user

@router_bases.get("", response_model=list[BaseEntityResponse])
def get_bases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == Role.ADMIN:
        return db.query(BaseEntity).all()
    else:
        return db.query(BaseEntity).filter(BaseEntity.id == current_user.base_id).all()

@router_bases.get("/{base_id}", response_model=BaseEntityResponse)
def get_base(base_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    PermissionService.enforce_base_scope(current_user, base_id)
    base = db.query(BaseEntity).filter(BaseEntity.id == base_id).first()
    if not base:
        raise NotFoundError("Base not found")
    return base
