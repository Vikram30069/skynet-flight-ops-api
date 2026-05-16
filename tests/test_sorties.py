import pytest
from datetime import datetime, timedelta
from app.db.models import Role, AircraftStatus, SortieStatus, DefectSeverity
from app.schemas.sortie import SortieCreate

def test_dispatcher_can_create_scheduled_sortie(client, auth_override, db_session):
    auth_override(Role.DISPATCHER, "base-1")
    
    # Setup aircraft
    from app.db.models import Aircraft
    ac = Aircraft(id="ac-1", registration="VT-ABC", aircraft_type="C172", base_id="base-1", status=AircraftStatus.READY)
    db_session.add(ac)
    db_session.commit()

    now = datetime.utcnow()
    payload = {
        "sortie_number": "S001",
        "cadet_id": "cadet-1",
        "instructor_id": "inst-1",
        "aircraft_id": "ac-1",
        "base_id": "base-1",
        "lesson_type": "Nav",
        "scheduled_start": now.isoformat(),
        "scheduled_end": (now + timedelta(hours=1)).isoformat()
    }
    
    response = client.post("/api/v1/sorties", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == SortieStatus.SCHEDULED.value

def test_dispatcher_can_release_scheduled_sortie(client, auth_override, db_session):
    auth_override(Role.DISPATCHER, "base-1")
    
    from app.db.models import Aircraft, Sortie
    ac = Aircraft(id="ac-1", registration="VT-ABC", aircraft_type="C172", base_id="base-1", status=AircraftStatus.SCHEDULED)
    now = datetime.utcnow()
    s = Sortie(id="s-1", sortie_number="S001", cadet_id="cadet-1", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-1", lesson_type="Nav", scheduled_start=now, scheduled_end=now, status=SortieStatus.SCHEDULED)
    db_session.add_all([ac, s])
    db_session.commit()
    
    response = client.patch("/api/v1/sorties/s-1/release")
    assert response.status_code == 200
    assert response.json()["status"] == SortieStatus.RELEASED.value

def test_dispatcher_can_mark_released_sortie_airborne(client, auth_override, db_session):
    auth_override(Role.DISPATCHER, "base-1")
    from app.db.models import Aircraft, Sortie
    ac = Aircraft(id="ac-1", registration="VT-ABC", aircraft_type="C172", base_id="base-1", status=AircraftStatus.SCHEDULED)
    s = Sortie(id="s-1", sortie_number="S001", cadet_id="cadet-1", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-1", lesson_type="Nav", scheduled_start=datetime.utcnow(), scheduled_end=datetime.utcnow(), status=SortieStatus.RELEASED)
    db_session.add_all([ac, s])
    db_session.commit()
    
    response = client.patch("/api/v1/sorties/s-1/airborne")
    assert response.status_code == 200
    assert response.json()["status"] == SortieStatus.AIRBORNE.value
    
def test_cannot_mark_scheduled_sortie_airborne_directly(client, auth_override, db_session):
    auth_override(Role.DISPATCHER, "base-1")
    from app.db.models import Aircraft, Sortie
    ac = Aircraft(id="ac-1", registration="VT-ABC", aircraft_type="C172", base_id="base-1", status=AircraftStatus.SCHEDULED)
    s = Sortie(id="s-1", sortie_number="S001", cadet_id="cadet-1", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-1", lesson_type="Nav", scheduled_start=datetime.utcnow(), scheduled_end=datetime.utcnow(), status=SortieStatus.SCHEDULED)
    db_session.add_all([ac, s])
    db_session.commit()
    
    response = client.patch("/api/v1/sorties/s-1/airborne")
    assert response.status_code == 400
    assert response.json()["error"] == "INVALID_STATE_TRANSITION"

def test_cannot_close_sortie_before_training_approval(client, auth_override, db_session):
    auth_override(Role.DISPATCHER, "base-1")
    from app.db.models import Aircraft, Sortie
    ac = Aircraft(id="ac-1", registration="VT-ABC", aircraft_type="C172", base_id="base-1", status=AircraftStatus.LANDED)
    s = Sortie(id="s-1", sortie_number="S001", cadet_id="cadet-1", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-1", lesson_type="Nav", scheduled_start=datetime.utcnow(), scheduled_end=datetime.utcnow(), status=SortieStatus.LANDED)
    db_session.add_all([ac, s])
    db_session.commit()
    
    response = client.patch("/api/v1/sorties/s-1/close")
    assert response.status_code == 400
    assert response.json()["error"] == "INVALID_STATE_TRANSITION"

def test_closed_sortie_cannot_be_released_again(client, auth_override, db_session):
    auth_override(Role.DISPATCHER, "base-1")
    from app.db.models import Aircraft, Sortie
    ac = Aircraft(id="ac-1", registration="VT-ABC", aircraft_type="C172", base_id="base-1", status=AircraftStatus.READY)
    s = Sortie(id="s-1", sortie_number="S001", cadet_id="cadet-1", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-1", lesson_type="Nav", scheduled_start=datetime.utcnow(), scheduled_end=datetime.utcnow(), status=SortieStatus.CLOSED)
    db_session.add_all([ac, s])
    db_session.commit()
    
    response = client.patch("/api/v1/sorties/s-1/release")
    assert response.status_code == 400
