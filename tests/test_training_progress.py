import pytest
from datetime import datetime
from app.db.models import Role, SortieStatus, TrainingProgressStatus

def test_assigned_instructor_can_submit_training_progress(client, auth_override, db_session):
    auth_override(Role.INSTRUCTOR, "base-1", user_id="inst-1")
    from app.db.models import Sortie
    s = Sortie(id="s-1", sortie_number="S001", cadet_id="cadet-1", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-1", lesson_type="Nav", scheduled_start=datetime.utcnow(), scheduled_end=datetime.utcnow(), status=SortieStatus.LANDED)
    db_session.add(s)
    db_session.commit()
    
    payload = {
        "sortie_id": "s-1",
        "lesson_type": "Nav",
        "maneuver_score": 4,
        "communication_score": 5,
        "situational_awareness_score": 4,
        "remarks": "Good flight"
    }
    # Create draft
    resp = client.post("/api/v1/training-progress", json=payload)
    assert resp.status_code == 200
    tp_id = resp.json()["id"]
    
    # Submit
    resp2 = client.patch(f"/api/v1/training-progress/{tp_id}/submit")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == TrainingProgressStatus.SUBMITTED.value

def test_non_assigned_instructor_cannot_submit_training_progress(client, auth_override, db_session):
    auth_override(Role.INSTRUCTOR, "base-1", user_id="inst-2") # Different instructor
    from app.db.models import Sortie
    s = Sortie(id="s-1", sortie_number="S001", cadet_id="cadet-1", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-1", lesson_type="Nav", scheduled_start=datetime.utcnow(), scheduled_end=datetime.utcnow(), status=SortieStatus.LANDED)
    db_session.add(s)
    db_session.commit()
    
    payload = {
        "sortie_id": "s-1",
        "lesson_type": "Nav",
        "maneuver_score": 4,
        "communication_score": 5,
        "situational_awareness_score": 4,
        "remarks": "Good flight"
    }
    resp = client.post("/api/v1/training-progress", json=payload)
    assert resp.status_code == 403

def test_cadet_cannot_submit_training_progress(client, auth_override, db_session):
    auth_override(Role.CADET, "base-1", user_id="cadet-1")
    payload = {
        "sortie_id": "s-1",
        "lesson_type": "Nav",
        "maneuver_score": 4,
        "communication_score": 5,
        "situational_awareness_score": 4,
        "remarks": "Good flight"
    }
    resp = client.post("/api/v1/training-progress", json=payload)
    assert resp.status_code == 403

def test_score_validation(client, auth_override, db_session):
    auth_override(Role.INSTRUCTOR, "base-1", user_id="inst-1")
    from app.db.models import Sortie
    s = Sortie(id="s-1", sortie_number="S001", cadet_id="cadet-1", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-1", lesson_type="Nav", scheduled_start=datetime.utcnow(), scheduled_end=datetime.utcnow(), status=SortieStatus.LANDED)
    db_session.add(s)
    db_session.commit()
    
    # Below 1
    payload = {
        "sortie_id": "s-1",
        "lesson_type": "Nav",
        "maneuver_score": 0,
        "communication_score": 5,
        "situational_awareness_score": 4,
        "remarks": "Good flight"
    }
    resp = client.post("/api/v1/training-progress", json=payload)
    assert resp.status_code == 422
    
    # Above 5
    payload["maneuver_score"] = 6
    resp = client.post("/api/v1/training-progress", json=payload)
    assert resp.status_code == 422
    
    # Null and "5" should work or fail based on schema, pydantic handles "5" nicely but lets test explicit error.
    payload["maneuver_score"] = None
    resp = client.post("/api/v1/training-progress", json=payload)
    assert resp.status_code == 200 # Allowed to be null during draft
