from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.errors import APIError
from app.api.routes import auth, users, aircraft, sorties, training_progress, defects, audit_logs
from app.api.routes.users import router_bases

app = FastAPI(title=settings.PROJECT_NAME)

@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request parameters",
            "details": exc.errors()
        }
    )

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router_users, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(router_bases, prefix=f"{settings.API_V1_STR}/bases", tags=["bases"])
app.include_router(aircraft.router, prefix=f"{settings.API_V1_STR}/aircraft", tags=["aircraft"])
app.include_router(sorties.router, prefix=f"{settings.API_V1_STR}/sorties", tags=["sorties"])
app.include_router(training_progress.router, prefix=f"{settings.API_V1_STR}/training-progress", tags=["training-progress"])
app.include_router(defects.router, prefix=f"{settings.API_V1_STR}/defects", tags=["defects"])
app.include_router(audit_logs.router, prefix=f"{settings.API_V1_STR}/audit-logs", tags=["audit-logs"])

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
