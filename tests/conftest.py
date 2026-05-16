import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import get_db, Base
from app.api.deps import get_current_user
from app.db.models import User, Role, BaseEntity

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=pool.StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def auth_override(client):
    def _override(role: Role, base_id: str, user_id: str = "mock-id"):
        def override_get_current_user():
            return User(id=user_id, role=role, base_id=base_id, email="mock@airman.com", full_name="Mock User")
        app.dependency_overrides[get_current_user] = override_get_current_user
    return _override
