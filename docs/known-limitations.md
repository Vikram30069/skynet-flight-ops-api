# Known Limitations

This section outlines aspects of the Skynet backend that are simplified for the scope of the internship assessment, and would need to be addressed before deploying to a real production environment.

## 1. Aircraft Time Before Overhaul (TBO) Tracking
- **Current State**: The `tbo_remaining_hours` field exists on the `Aircraft` model.
- **Limitation**: There is currently no logic that automatically deducts flight hours (calculated from `actual_end - actual_start`) from this value when a sortie is marked as `CLOSED`. In a real system, the closure of a sortie should trigger an update to the aircraft's TBO.

## 2. Concurrency and Race Conditions
- **Current State**: The system uses synchronous database queries and does not explicitly implement database locks (e.g., `SELECT ... FOR UPDATE`).
- **Limitation**: In a highly concurrent environment where multiple dispatchers might try to assign the same aircraft to overlapping sorties at the exact same millisecond, a race condition could occur. Optimistic concurrency control (via a version column) or pessimistic locking would be needed for absolute safety.

## 3. Rate Limiting and Security
- **Current State**: Basic JWT authentication is implemented and passwords are hashed.
- **Limitation**: The system lacks rate limiting (e.g., via Redis) to prevent brute-force attacks on the `/auth/login` endpoint. It also lacks refresh token handling, meaning users must log in again when their token expires.

## 4. Complex Database Queries and Pagination
- **Current State**: Endpoints like `GET /sorties` return all rows (filtered by base scope).
- **Limitation**: There is no pagination implemented (e.g., `limit` and `offset`). If the flight school has 10,000 sorties, this API call will become extremely slow and memory-intensive. Production APIs must always implement pagination for list endpoints.

## 5. Synchronous Architecture
- **Current State**: The application uses synchronous SQLAlchemy (`SessionLocal`).
- **Limitation**: While FastAPI is built on ASGI and supports high concurrency, using blocking synchronous database calls limits its asynchronous potential. Moving to `asyncpg` and `AsyncSession` would dramatically improve throughput.
