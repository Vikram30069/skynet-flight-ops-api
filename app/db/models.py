import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    DISPATCHER = "DISPATCHER"
    INSTRUCTOR = "INSTRUCTOR"
    CFI = "CFI"
    CADET = "CADET"
    MAINTENANCE_OFFICER = "MAINTENANCE_OFFICER"

class AircraftStatus(str, enum.Enum):
    READY = "READY"
    SCHEDULED = "SCHEDULED"
    AIRBORNE = "AIRBORNE"
    LANDED = "LANDED"
    GROUNDED = "GROUNDED"
    MAINTENANCE = "MAINTENANCE"

class SortieStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    RELEASED = "RELEASED"
    AIRBORNE = "AIRBORNE"
    LANDED = "LANDED"
    TRAINING_SUBMITTED = "TRAINING_SUBMITTED"
    TRAINING_APPROVED = "TRAINING_APPROVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    AIRCRAFT_GROUNDED = "AIRCRAFT_GROUNDED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"

class TrainingProgressStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class DefectSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DefectStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    DEFERRED = "DEFERRED"

class BaseEntity(Base):
    __tablename__ = "bases"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    location = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    users = relationship("User", back_populates="base")
    aircraft = relationship("Aircraft", back_populates="base")
    sorties = relationship("Sortie", back_populates="base")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False) # Not in original prompt but needed for auth
    role = Column(Enum(Role), nullable=False)
    base_id = Column(String, ForeignKey("bases.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    base = relationship("BaseEntity", back_populates="users")

class Aircraft(Base):
    __tablename__ = "aircraft"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    registration = Column(String, unique=True, index=True, nullable=False)
    aircraft_type = Column(String, nullable=False)
    base_id = Column(String, ForeignKey("bases.id"), nullable=False)
    status = Column(Enum(AircraftStatus), default=AircraftStatus.READY, nullable=False)
    tbo_remaining_hours = Column(Integer, default=2000)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    base = relationship("BaseEntity", back_populates="aircraft")
    sorties = relationship("Sortie", back_populates="aircraft")
    defects = relationship("Defect", back_populates="aircraft")

class Sortie(Base):
    __tablename__ = "sorties"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    sortie_number = Column(String, unique=True, index=True, nullable=False)
    cadet_id = Column(String, ForeignKey("users.id"), nullable=False)
    instructor_id = Column(String, ForeignKey("users.id"), nullable=False)
    aircraft_id = Column(String, ForeignKey("aircraft.id"), nullable=False)
    base_id = Column(String, ForeignKey("bases.id"), nullable=False)
    lesson_type = Column(String, nullable=False)
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(SortieStatus), default=SortieStatus.SCHEDULED, nullable=False)
    delay_minutes = Column(Integer, default=0)
    cancel_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    base = relationship("BaseEntity", back_populates="sorties")
    aircraft = relationship("Aircraft", back_populates="sorties")
    cadet = relationship("User", foreign_keys=[cadet_id])
    instructor = relationship("User", foreign_keys=[instructor_id])
    training_progress = relationship("TrainingProgress", back_populates="sortie", uselist=False)
    defects = relationship("Defect", back_populates="sortie")

class TrainingProgress(Base):
    __tablename__ = "training_progress"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    sortie_id = Column(String, ForeignKey("sorties.id"), unique=True, nullable=False)
    cadet_id = Column(String, ForeignKey("users.id"), nullable=False)
    instructor_id = Column(String, ForeignKey("users.id"), nullable=False)
    lesson_type = Column(String, nullable=False)
    maneuver_score = Column(Integer, nullable=True)
    communication_score = Column(Integer, nullable=True)
    situational_awareness_score = Column(Integer, nullable=True)
    remarks = Column(Text, nullable=True)
    status = Column(Enum(TrainingProgressStatus), default=TrainingProgressStatus.DRAFT, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    sortie = relationship("Sortie", back_populates="training_progress")
    cadet = relationship("User", foreign_keys=[cadet_id])
    instructor = relationship("User", foreign_keys=[instructor_id])
    approver = relationship("User", foreign_keys=[approved_by])

class Defect(Base):
    __tablename__ = "defects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    aircraft_id = Column(String, ForeignKey("aircraft.id"), nullable=False)
    sortie_id = Column(String, ForeignKey("sorties.id"), nullable=True)
    reported_by = Column(String, ForeignKey("users.id"), nullable=False)
    severity = Column(Enum(DefectSeverity), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(DefectStatus), default=DefectStatus.OPEN, nullable=False)
    resolved_by = Column(String, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    aircraft = relationship("Aircraft", back_populates="defects")
    sortie = relationship("Sortie", back_populates="defects")
    reporter = relationship("User", foreign_keys=[reported_by])
    resolver = relationship("User", foreign_keys=[resolved_by])

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    actor_id = Column(String, nullable=True)
    actor_role = Column(String, nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    old_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
