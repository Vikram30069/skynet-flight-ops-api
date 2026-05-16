import pytest
from datetime import datetime, timedelta
from app.db.models import Role, AircraftStatus, SortieStatus, DefectSeverity

def test_grounded_aircraft_cannot_be_assigned_to_new_sortie(client, auth_override, db_session):
    auth_override(Role.DISPATCHER, "base-1")
    from app.db.models import Aircraft
    ac = Aircraft(id="ac-1", registration="VT-ABC", aircraft_type="C172", base_id="base-1", status=AircraftStatus.GROUNDED)
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
    assert response.status_code == 409
    assert "Grounded aircraft cannot be assigned" in response.json()["message"]

def test_grounded_aircraft_cannot_be_released(client, auth_override, db_session):
    auth_override(Role.DISPATCHER, "base-1")
    from app.db.models import Aircraft, Sortie
    ac = Aircraft(id="ac-1", registration="VT-ABC", aircraft_type="C172", base_id="base-1", status=AircraftStatus.GROUNDED)
    s = Sortie(id="s-1", sortie_number="S001", cadet_id="cadet-1", instructor_id="inst-1", aircraft_id="ac-1", base_id="base-1", lesson_type="Nav", scheduled_start=datetime.utcnow(), scheduled_end=datetime.utcnow(), status=SortieStatus.SCHEDULED)
    db_session.add_all([ac, s])
    db_session.commit()
    
    response = client.patch("/api/v1/sorties/s-1/release")
    assert response.status_code == 409
    assert "Grounded aircraft cannot be released" in response.json()["message"]

def test_critical_defect_grounds_aircraft(client, auth_override, db_session):
    auth_override(Role.MAINTENANCE_OFFICER, "base-1")
    from app.db.models import Aircraft
    ac = Aircraft(id="ac-1", registration="VT-ABC", aircraft_type="C172", base_id="base-1", status=AircraftStatus.READY)
    db_session.add(ac)
    db_session.commit()
    
    payload = {
        "aircraft_id": "ac-1",
        "severity": DefectSeverity.CRITICAL.value,
        "description": "Engine failure"
    }
    response = client.post("/api/v1/defects", json=payload)
    assert response.status_code == 200
    
    db_session.refresh(ac)
    assert ac.status == AircraftStatus.GROUNDED

def test_aircraft_cannot_become_ready_until_defect_resolved(client, auth_override, db_session):
    auth_override(Role.MAINTENANCE_OFFICER, "base-1", user_id="maint-1")
    from app.db.models import Aircraft, Defect, DefectStatus
    ac = Aircraft(id="ac-1", registration="VT-ABC", aircraft_type="C172", base_id="base-1", status=AircraftStatus.GROUNDED)
    d = Defect(id="d-1", aircraft_id="ac-1", reported_by="maint-1", severity=DefectSeverity.CRITICAL, description="Bad", status=DefectStatus.OPEN)
    db_session.add_all([ac, d])
    db_session.commit()
    
    response = client.patch("/api/v1/aircraft/ac-1/ready")
    assert response.status_code == 409
    assert "open critical/high defects exist" in response.json()["message"]
