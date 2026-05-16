import datetime
import uuid
from sqlalchemy.orm import Session
from app.db.database import engine, Base, SessionLocal
from app.db.models import (
    BaseEntity, User, Aircraft, Sortie, TrainingProgress, Defect, AuditLog,
    Role, AircraftStatus, SortieStatus, TrainingProgressStatus, DefectSeverity, DefectStatus
)
from app.core.security import get_password_hash

def generate_uuid():
    return str(uuid.uuid4())

def seed_db():
    print("Creating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 1. Bases
        print("Seeding Bases...")
        base_a = BaseEntity(id=generate_uuid(), name="Alpha Base", code="ALPHA", location="City A")
        base_b = BaseEntity(id=generate_uuid(), name="Beta Base", code="BETA", location="City B")
        db.add_all([base_a, base_b])
        db.commit()

        # 2. Users
        print("Seeding Users...")
        admin = User(id=generate_uuid(), full_name="Admin User", email="admin@airman.com", password_hash=get_password_hash("password"), role=Role.ADMIN, base_id=base_a.id)
        dispatcher = User(id=generate_uuid(), full_name="Dispatch Officer", email="dispatch@airman.com", password_hash=get_password_hash("password"), role=Role.DISPATCHER, base_id=base_a.id)
        instructor = User(id=generate_uuid(), full_name="Capt. Rao", email="rao@airman.com", password_hash=get_password_hash("password"), role=Role.INSTRUCTOR, base_id=base_a.id)
        cfi = User(id=generate_uuid(), full_name="Chief Flying Instructor", email="cfi@airman.com", password_hash=get_password_hash("password"), role=Role.CFI, base_id=base_a.id)
        cadet = User(id=generate_uuid(), full_name="Arjun Menon", email="arjun@airman.com", password_hash=get_password_hash("password"), role=Role.CADET, base_id=base_a.id)
        maintenance = User(id=generate_uuid(), full_name="Maintenance Officer", email="maint@airman.com", password_hash=get_password_hash("password"), role=Role.MAINTENANCE_OFFICER, base_id=base_a.id)
        
        db.add_all([admin, dispatcher, instructor, cfi, cadet, maintenance])
        db.commit()

        # 3. Aircraft
        print("Seeding Aircraft...")
        ac1 = Aircraft(id=generate_uuid(), registration="VT-ABC", aircraft_type="Cessna 172", base_id=base_a.id, status=AircraftStatus.READY)
        ac2 = Aircraft(id=generate_uuid(), registration="VT-SKY", aircraft_type="Piper PA-28", base_id=base_a.id, status=AircraftStatus.GROUNDED)
        ac3 = Aircraft(id=generate_uuid(), registration="VT-AIR", aircraft_type="Diamond DA40", base_id=base_a.id, status=AircraftStatus.READY)
        
        db.add_all([ac1, ac2, ac3])
        db.commit()

        # 4. Sorties
        print("Seeding Sorties...")
        now = datetime.datetime.utcnow()
        s1 = Sortie(id=generate_uuid(), sortie_number="S001", cadet_id=cadet.id, instructor_id=instructor.id, aircraft_id=ac1.id, base_id=base_a.id, lesson_type="Circuit", scheduled_start=now, scheduled_end=now + datetime.timedelta(hours=1), status=SortieStatus.SCHEDULED)
        s2 = Sortie(id=generate_uuid(), sortie_number="S002", cadet_id=cadet.id, instructor_id=instructor.id, aircraft_id=ac1.id, base_id=base_a.id, lesson_type="Navigation", scheduled_start=now, scheduled_end=now + datetime.timedelta(hours=1), status=SortieStatus.RELEASED)
        s3 = Sortie(id=generate_uuid(), sortie_number="S003", cadet_id=cadet.id, instructor_id=instructor.id, aircraft_id=ac3.id, base_id=base_a.id, lesson_type="Stalls", scheduled_start=now, scheduled_end=now + datetime.timedelta(hours=1), status=SortieStatus.AIRBORNE, actual_start=now)
        s4 = Sortie(id=generate_uuid(), sortie_number="S004", cadet_id=cadet.id, instructor_id=instructor.id, aircraft_id=ac3.id, base_id=base_a.id, lesson_type="Emergency", scheduled_start=now, scheduled_end=now + datetime.timedelta(hours=1), status=SortieStatus.LANDED, actual_start=now, actual_end=now + datetime.timedelta(minutes=45))
        s5 = Sortie(id=generate_uuid(), sortie_number="S005", cadet_id=cadet.id, instructor_id=instructor.id, aircraft_id=ac1.id, base_id=base_a.id, lesson_type="Instrument", scheduled_start=now, scheduled_end=now + datetime.timedelta(hours=1), status=SortieStatus.TRAINING_SUBMITTED, actual_start=now, actual_end=now + datetime.timedelta(hours=1))

        db.add_all([s1, s2, s3, s4, s5])
        db.commit()

        # Update aircraft statuses to reflect sorties (for realism)
        ac1.status = AircraftStatus.LANDED # for S5
        ac3.status = AircraftStatus.AIRBORNE # for S3
        db.commit()

        # 5. Training Progress
        print("Seeding Training Progress...")
        tp1 = TrainingProgress(id=generate_uuid(), sortie_id=s5.id, cadet_id=cadet.id, instructor_id=instructor.id, lesson_type="Instrument", maneuver_score=4, communication_score=5, situational_awareness_score=4, remarks="Good flight", status=TrainingProgressStatus.SUBMITTED, submitted_at=now)
        
        # We need a CLOSED sortie for the second training progress to be APPROVED
        s6 = Sortie(id=generate_uuid(), sortie_number="S006", cadet_id=cadet.id, instructor_id=instructor.id, aircraft_id=ac1.id, base_id=base_a.id, lesson_type="Solo Check", scheduled_start=now, scheduled_end=now + datetime.timedelta(hours=1), status=SortieStatus.CLOSED, actual_start=now, actual_end=now + datetime.timedelta(minutes=50))
        db.add(s6)
        db.commit()

        tp2 = TrainingProgress(id=generate_uuid(), sortie_id=s6.id, cadet_id=cadet.id, instructor_id=instructor.id, lesson_type="Solo Check", maneuver_score=5, communication_score=5, situational_awareness_score=5, remarks="Cleared for solo", status=TrainingProgressStatus.APPROVED, submitted_at=now, approved_by=cfi.id, approved_at=now)
        db.add_all([tp1, tp2])
        db.commit()

        # 6. Defects
        print("Seeding Defects...")
        d1 = Defect(id=generate_uuid(), aircraft_id=ac2.id, reported_by=instructor.id, severity=DefectSeverity.CRITICAL, description="Engine noise", status=DefectStatus.OPEN)
        d2 = Defect(id=generate_uuid(), aircraft_id=ac3.id, reported_by=maintenance.id, severity=DefectSeverity.LOW, description="Scratch on left wing", status=DefectStatus.RESOLVED, resolved_by=maintenance.id, resolved_at=now)
        
        db.add_all([d1, d2])
        db.commit()

        print("Seeding completed successfully.")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
