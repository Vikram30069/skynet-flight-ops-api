import pytest
from datetime import datetime
from app.db.models import Role, SortieStatus, DefectSeverity

def test_cadet_can_view_own_sortie_only(client, auth_override, db_session):
    auth_override(Role.CADET, "base-1", user_id="cadet-1")
    from app.db.models import Sortie
    s1 = Sortie(id="s-1", sortie_number="S001", cadet_id="cadet-1", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-1", lesson_type="Nav", scheduled_start=datetime.utcnow(), scheduled_end=datetime.utcnow(), status=SortieStatus.SCHEDULED)
    s2 = Sortie(id="s-2", sortie_number="S002", cadet_id="cadet-2", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-1", lesson_type="Nav", scheduled_start=datetime.utcnow(), scheduled_end=datetime.utcnow(), status=SortieStatus.SCHEDULED)
    db_session.add_all([s1, s2])
    db_session.commit()
    
    resp = client.get("/api/v1/sorties/s-1")
    assert resp.status_code == 200
    
    resp2 = client.get("/api/v1/sorties/s-2")
    assert resp2.status_code == 403

def test_maintenance_officer_cannot_approve_training_progress(client, auth_override, db_session):
    auth_override(Role.MAINTENANCE_OFFICER, "base-1")
    resp = client.patch("/api/v1/training-progress/tp-1/approve")
    assert resp.status_code == 403

def test_admin_can_access_all(client, auth_override, db_session):
    auth_override(Role.ADMIN, "base-1") # Admin belongs to base-1
    from app.db.models import Sortie
    s1 = Sortie(id="s-1", sortie_number="S001", cadet_id="cadet-1", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-2", lesson_type="Nav", scheduled_start=datetime.utcnow(), scheduled_end=datetime.utcnow(), status=SortieStatus.SCHEDULED)
    db_session.add(s1)
    db_session.commit()
    
    resp = client.get("/api/v1/sorties/s-1")
    assert resp.status_code == 200 # Admin bypasses base scope

def test_base_a_dispatcher_cannot_access_base_b_sortie(client, auth_override, db_session):
    auth_override(Role.DISPATCHER, "base-1")
    from app.db.models import Sortie
    s1 = Sortie(id="s-1", sortie_number="S001", cadet_id="cadet-1", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-2", lesson_type="Nav", scheduled_start=datetime.utcnow(), scheduled_end=datetime.utcnow(), status=SortieStatus.SCHEDULED)
    db_session.add(s1)
    db_session.commit()
    
    resp = client.get("/api/v1/sorties/s-1")
    assert resp.status_code == 403
