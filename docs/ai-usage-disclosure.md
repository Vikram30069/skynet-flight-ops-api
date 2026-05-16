# AI Usage Disclosure

## 1. Did you use AI tools? If yes, where?
Yes. AI tools were used to rapidly generate boilerplate code, Pydantic schemas, and foundational test fixtures to meet the 24-hour deadline.

## 2. What did AI generate?
- FastAPI router scaffolding.
- SQLAlchemy model definitions.
- Pytest setups (`conftest.py`) and standard CRUD assertions.

## 3. What did you manually review or change?
The entire `services/` layer was heavily structured and reviewed manually to ensure strict enforcement of aviation business rules (e.g., verifying that a sortie cannot transition to CLOSED without CFI approval, and that a critical defect automatically grounds the assigned aircraft).

## 4. Which AI-generated suggestion did you reject and why?
I rejected AI suggestions to handle State Transitions inside the FastAPI Router files. I moved that logic to a dedicated `SortieService` and `AircraftService` to ensure the API layer remains stateless and easily testable, and to prevent scattered business logic.

## 5. Which part of the project did you personally design?
The architectural split between Controllers (Routes) and Services, the RBAC/Base-scope permission checker (`PermissionService`), and the strict mapping of invalid state transitions.

## 6. Which part are you least confident about?
The `tbo_remaining_hours` logic on Aircraft. Currently, it exists as a column but there is no automated trigger deducting flight hours (actual_end - actual_start) from the aircraft's TBO upon sortie closure. This would need to be added for a production system.

## 7. Pick one backend route and explain it line by line.
**`PATCH /sorties/{sortie_id}/release`**
```python
@router.patch("/{sortie_id}/release", response_model=SortieResponse)
def release_sortie(sortie_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Fetch the sortie from the DB; throws 404 if missing
    sortie = SortieService.get_sortie(db, sortie_id)
    # Check if the current user belongs to the same base as the sortie, throwing 403 if not.
    PermissionService.enforce_base_scope(current_user, sortie.base_id)
    # Delegate to the service layer to validate state transition, update aircraft, log audit, and save.
    return SortieService.release_sortie(db, sortie_id, current_user)
```

## 8. Pick one business rule and explain how your code enforces it.
**Rule**: "A sortie with grounded aircraft must not be closed unless the workflow is documented through defect/recovery resolution."
**Enforcement**: In `SortieService.close_sortie()`, before allowing the transition to `CLOSED`, we check the aircraft's status. If the associated aircraft is `GROUNDED`, we throw an `InvalidStateTransitionError` specifically stating it cannot be closed. The maintenance workflow must mark the aircraft `READY` (by resolving defects) before the sortie can finally close.

## 9. Pick one test and explain why it matters.
**`test_cannot_close_sortie_before_training_approval`**
It ensures that Dispatchers or admins cannot accidentally finalize a flight record before the CFI signs off on the cadet's progress. In a flight academy, auditability of training hours is critical for pilot licensing. If this rule broke, cadets could log unverified hours.

## 10. What would break first if this backend had 10 flight schools using it?
Database contention and ID collisions. Using standard serial integers could lead to enumeration attacks or scaling limits. UUIDs solve the collision/enumeration part, but base isolation queries could become slow. We would need to add indexes on `base_id` across all tables, and eventually implement proper row-level security (RLS) in PostgreSQL.
