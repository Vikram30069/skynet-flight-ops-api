# Architecture and Business Rules

## 1. Backend Structure
The application follows a standard modular FastAPI structure:
- **`core/`**: Central configuration, security (JWT, hashing), error classes, and permission enforcement logic.
- **`db/`**: SQLAlchemy models and database connection logic.
- **`schemas/`**: Pydantic models for request/response validation.
- **`services/`**: The core business logic layer. Services (e.g. `SortieService`) contain all rules, state transition validation, and audit logging to keep the API routers clean.
- **`api/routes/`**: FastAPI endpoints that depend on the service layer.

## 2. Database Design
We use PostgreSQL via SQLAlchemy.
- **Relationships**: `Sorties` tie together `Aircraft`, `User` (Cadet), and `User` (Instructor). `Defects` tie to `Aircraft` and potentially a `Sortie`.
- **Enums**: We strictly use PostgreSQL Enums for Statuses and Roles to enforce data integrity at the database level.
- **UUIDs**: Primary keys are UUIDs to prevent enumeration attacks and ensure scalability across distributed bases.

## 3. Role/Permission Design
Role-Based Access Control (RBAC) and Base-Scoping are enforced via the `PermissionService`.
- **Role Enforcement**: Done using dependencies in routes or direct checks in services (e.g. `if current_user.role not in [Role.ADMIN, Role.DISPATCHER]`).
- **Base-Scoping**: Non-admin users are restricted to entities belonging to their `base_id`. The service checks `if user.base_id != entity.base_id: raise ForbiddenError()`.

## 4. State Transition Handling
State transitions are defined by a strict state machine dictionary in `SortieService`. 
Any deviation throws a `400 INVALID_STATE_TRANSITION`. This guarantees that you cannot skip steps (like going from SCHEDULED to AIRBORNE).

## 5. Audit Log Design
An `AuditService` acts as a central hub for logging. Any meaningful state change (transitions, defects, approvals) calls `AuditService.log_action()` which serializes old and new values into the `audit_logs` table.

## 6. Error Handling Design
A custom `APIError` class extends `HTTPException` to guarantee that all errors return a uniform JSON schema containing `{"error": "CODE", "message": "human readable"}`. This prevents raw stack traces from leaking to the frontend.

## 7. How Seed Data Works
The `seed.py` script uses SQLAlchemy's ORM to drop all tables, create them fresh, and populate them with the exact data requested in the prompt. It properly hashes passwords and creates relationships so the app is instantly usable for testing.

## 8. Backend vs Frontend Responsibility
The frontend is responsible for hiding buttons (e.g. hiding "Release" from a Cadet), but the **backend is the ultimate source of truth**. Even if a malicious user uses Postman to send a PATCH request to release a sortie as a Cadet, the backend `PermissionService` intercepts and blocks it.

## 9. Known Trade-offs
- **Transactions**: For simplicity in this assessment, some complex workflows (like creating a defect and grounding an aircraft) happen sequentially in a single synchronous thread. In high-concurrency systems, using explicit transaction blocks or sagas might be safer.
- **Synchronous DB**: We used synchronous SQLAlchemy (`SessionLocal`). For a real production app scaling to thousands of reqs/sec, `asyncpg` and AsyncSession would be better.
