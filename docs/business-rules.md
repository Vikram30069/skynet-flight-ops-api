# Business Rules

This document outlines the core business logic rules enforced by the backend, regardless of what the frontend UI permits.

## 1. Sortie State Rules
Valid transitions:
- `SCHEDULED` → `RELEASED`
- `RELEASED` → `AIRBORNE`
- `AIRBORNE` → `LANDED`
- `LANDED` → `TRAINING_SUBMITTED`
- `TRAINING_SUBMITTED` → `TRAINING_APPROVED`
- `TRAINING_APPROVED` → `CLOSED`

**Exceptions enforced:**
- Any invalid transition (e.g. `SCHEDULED` → `AIRBORNE`) returns `400 INVALID_STATE_TRANSITION`.
- A sortie with a `GROUNDED` aircraft cannot be released or assigned.
- A sortie cannot be closed unless training is approved.

## 2. Aircraft Readiness Rules
- **Assignment**: Grounded aircraft throw `409 Conflict` if assigned to a new sortie.
- **Auto-State Updates**: Aircraft state mirrors the sortie state. When a sortie goes `AIRBORNE`, the aircraft becomes `AIRBORNE`.
- **Defects**: Submitting a `CRITICAL` or `HIGH` defect automatically moves the aircraft to `GROUNDED`.
- **Readiness Check**: Aircraft cannot transition back to `READY` until all critical/high open defects are resolved or deferred.

## 3. Training Progress Rules
- **Submission**: Only the assigned instructor (or admin) can create/submit. Cadets cannot submit or edit.
- **Validation**: Scores are strictly enforced as integers `1` through `5`. Remarks are mandatory upon submission.
- **Approval**: Only the CFI (or Admin) can transition training from `SUBMITTED` to `APPROVED` or `REJECTED`.
- **Visibility**: Cadets can only view their own training progress, and only *after* it has reached `APPROVED` status. Drafts are hidden from cadets.

## 4. RBAC Rules
Strict Role-Based Access Control limits what APIs a token can hit:
- `ADMIN`: Global access.
- `DISPATCHER`: Can manage sortie state, but cannot approve training.
- `INSTRUCTOR`: Can only submit training for assigned sorties.
- `CFI`: Can approve/reject training.
- `CADET`: Read-only access to own sorties and approved training.
- `MAINTENANCE_OFFICER`: Can manage aircraft status and resolve defects.

## 5. Base Scoped Rules
Records are tied to a `base_id`. The backend checks the JWT token's `base_id` against the resource's `base_id`. If a dispatcher from Base A tries to access a Sortie from Base B, a `403 FORBIDDEN` is thrown. Admins bypass this.

## 6. Audit Logging
Audit logs are created for critical actions using `AuditService.log_action()`. It captures `actor_id`, `actor_role`, `action`, `entity_type`, `entity_id`, `old_value`, and `new_value`.
