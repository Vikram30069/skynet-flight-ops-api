# Skynet Flight Operations API

This is the backend service for Skynet, AIRMAN's Flight School / Aviation Academy Operations SaaS. It handles strict aviation workflow rules, role-based access control, aircraft readiness, and training progress.

## Tech Stack
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL (via SQLAlchemy & async ready structure)
- **Validation**: Pydantic v2
- **Testing**: Pytest
- **Auth**: JWT (Passlib/Bcrypt)
- **Containerization**: Docker & Docker Compose

## Setup Instructions

### 1. Environment Variables
No `.env` file is strictly required for local testing as defaults are provided in `core/config.py`, but you can override them:
```env
DATABASE_URL=postgresql://airman:airman_password@localhost:5432/skynet
SECRET_KEY=your_secure_secret_key
```

### 2. How to Run Backend (Docker - Recommended)
To spin up both the FastAPI application and PostgreSQL database:
```bash
docker-compose up --build
```
The API will be available at `http://localhost:8000/docs` (Swagger UI).

### 3. How to Run Migrations / Create Tables
Tables are auto-created when you run the seed script. Alembic can be initialized for production migrations.
```bash
# To populate the database with tables and seed data:
docker-compose exec api python -m app.db.seed
```

### 4. How to Seed Data
Run the seed script inside the docker container:
```bash
docker-compose exec api python -m app.db.seed
```
This will create 2 bases, 3 aircraft, 6 users (Admin, Dispatcher, Instructor, CFI, Cadet, Maintenance), 5 sorties, defects, and training logs.

### 5. How to Run Tests
The test suite uses an in-memory SQLite database to run extremely fast without affecting your Postgres data.
```bash
docker-compose exec api pytest
```

## API Summary
Full documentation can be viewed interactively at `/docs` when the server is running, or in `docs/api-contract.md`.
- `POST /auth/login` - Obtain JWT
- `PATCH /sorties/{id}/release` - Dispatch workflow
- `POST /training-progress` - Instructor grading
- `POST /defects` - Maintenance logging

## User Roles and Permissions
Implemented roles: `ADMIN`, `DISPATCHER`, `INSTRUCTOR`, `CFI`, `CADET`, `MAINTENANCE_OFFICER`.
Permissions strictly follow the assignment guidelines (e.g. Cadets can only read own approved training).

## Business Rules Implemented
- Strict state machine for Sortie status (`SCHEDULED` -> `RELEASED` -> `AIRBORNE` -> `LANDED` -> `TRAINING_SUBMITTED` -> `TRAINING_APPROVED` -> `CLOSED`).
- Aircraft auto-grounding on critical defects.
- Cross-base data isolation (Base A cannot see Base B).
- Sortie closure blocked without CFI training approval.

## Known Limitations
- Aircraft TBO (Time Before Overhaul) is static; it does not auto-decrement based on sortie flight time yet.
- Rate limiting is not fully implemented.

## What I would improve with more time
- Add `asyncpg` and migrate SQLAlchemy to `AsyncSession` for massive concurrency scaling.
- Integrate Alembic migrations fully for schema evolution.
- Add Row-Level Security (RLS) at the PostgreSQL level for foolproof tenant isolation.

## AI Usage Disclosure
Please see `docs/ai-usage-disclosure.md` for answers to the AI transparency questions.
