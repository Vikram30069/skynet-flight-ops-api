import pytest
from datetime import datetime
from app.db.models import Role, AircraftStatus, DefectSeverity

def test_audit_log_created_for_defect(client, auth_override, db_session):
    auth_override(Role.MAINTENANCE_OFFICER, "base-1", user_id="maint-1")
    from app.db.models import Aircraft
    ac = Aircraft(id="ac-1", registration="VT-ABC", aircraft_type="C172", base_id="base-1", status=AircraftStatus.READY)
    db_session.add(ac)
    db_session.commit()
    
    payload = {
        "aircraft_id": "ac-1",
        "severity": DefectSeverity.CRITICAL.value,
        "description": "Engine failure"
    }
    client.post("/api/v1/defects", json=payload)
    
    # Check audit log as Admin
    auth_override(Role.ADMIN, "base-1")
    resp = client.get("/api/v1/audit-logs?entity_type=defect")
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) >= 1
    
    log = logs[0]
    assert log["action"] == "DEFECT_CREATED"
    assert log["actor_role"] == Role.MAINTENANCE_OFFICER.value
    assert "Engine failure" in log["new_value"]
