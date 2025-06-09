import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Use test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create fresh DB for tests
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Override DB dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module")
def test_user():
    user_data = {"email": "test@example.com", "password": "testpass"}
    client.post("/auth/register", json=user_data)
    response = client.post("/auth/login", json=user_data)
    token = response.json()["access_token"]
    return {"token": token, "headers": {"Authorization": f"Bearer {token}"}}

def test_access_books_with_token(test_user):
    response = client.get("/books", headers=test_user["headers"])
    assert response.status_code == 200

def test_access_books_without_token():
    response = client.get("/books")
    assert response.status_code == 401
