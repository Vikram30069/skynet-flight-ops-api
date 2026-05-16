# Skynet API Contract

## Overview
Base URL: `/api/v1`
Authentication: Bearer Token (JWT)

All requests to secured endpoints require an `Authorization: Bearer <token>` header.

## Endpoint List

### 1. Create Sortie
* **Method**: `POST`
* **Path**: `/sorties`
* **Auth/Roles**: `DISPATCHER`, `ADMIN`
* **Request Body**:
  ```json
  {
    "sortie_number": "S001",
    "cadet_id": "uuid",
    "instructor_id": "uuid",
    "aircraft_id": "uuid",
    "base_id": "uuid",
    "lesson_type": "Nav",
    "scheduled_start": "2026-05-17T10:00:00Z",
    "scheduled_end": "2026-05-17T11:00:00Z"
  }
  ```
* **Response Body**:
  ```json
  {
    "id": "uuid",
    "sortie_number": "S001",
    "status": "SCHEDULED",
    "created_at": "...",
    "updated_at": "..."
  }
  ```
* **Errors**: `403 FORBIDDEN`, `409 CONFLICT` (if aircraft is grounded or overlapping).

### 2. Release Sortie
* **Method**: `PATCH`
* **Path**: `/sorties/{id}/release`
* **Auth/Roles**: `DISPATCHER`, `ADMIN`
* **Request Body**: None
* **Response Body**: Same as Create Sortie, but `status: "RELEASED"`.
* **Errors**: `400 INVALID_STATE_TRANSITION`, `409 CONFLICT`.

### 3. Mark Sortie Airborne
* **Method**: `PATCH`
* **Path**: `/sorties/{id}/airborne`
* **Auth/Roles**: `DISPATCHER`, `ADMIN`
* **Request Body**: None
* **Response Body**: Same as Create Sortie, but `status: "AIRBORNE"`.
* **Errors**: `400 INVALID_STATE_TRANSITION`.

### 4. Submit Training Progress
* **Method**: `POST`
* **Path**: `/training-progress`
* **Auth/Roles**: `INSTRUCTOR`, `ADMIN`
* **Request Body**:
  ```json
  {
    "sortie_id": "uuid",
    "lesson_type": "Nav",
    "maneuver_score": 4,
    "communication_score": 5,
    "situational_awareness_score": 3,
    "remarks": "Good flight, watch crosswind"
  }
  ```
* **Response Body**:
  ```json
  {
    "id": "uuid",
    "status": "DRAFT",
    "remarks": "Good flight, watch crosswind"
  }
  ```
* **Errors**: `403 FORBIDDEN`, `422 VALIDATION_ERROR` (if scores out of bounds).

### 5. Approve Training Progress
* **Method**: `PATCH`
* **Path**: `/training-progress/{id}/approve`
* **Auth/Roles**: `CFI`, `ADMIN`
* **Request Body**: None
* **Response Body**: Progress object with `status: "APPROVED"`.
* **Errors**: `403 FORBIDDEN`, `409 CONFLICT` (if not submitted).

### 6. Report Defect
* **Method**: `POST`
* **Path**: `/defects`
* **Auth/Roles**: `ALL` (assuming open to any authorized user, but resolvers are restricted)
* **Request Body**:
  ```json
  {
    "aircraft_id": "uuid",
    "severity": "CRITICAL",
    "description": "Engine vibrations"
  }
  ```
* **Response Body**: Defect object.
* **Errors**: `422 VALIDATION_ERROR`.

### 7. Ground Aircraft
* **Method**: `PATCH`
* **Path**: `/aircraft/{id}/ground`
* **Auth/Roles**: `MAINTENANCE_OFFICER`, `DISPATCHER`, `ADMIN`
* **Request Body**: None
* **Response Body**: Aircraft object with `status: "GROUNDED"`.

### 8. Get Audit Logs
* **Method**: `GET`
* **Path**: `/audit-logs?entity_type={type}&entity_id={id}`
* **Auth/Roles**: `ADMIN`, `CFI`, `DISPATCHER`
* **Response Body**: Array of logs.
