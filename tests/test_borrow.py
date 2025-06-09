import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module")
def test_auth_token():
    user = {"email": "borrower@example.com", "password": "securepass"}
    client.post("/auth/register", json=user)
    login = client.post("/auth/login", json=user)
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_borrow_book_success(test_auth_token):
    book_res = client.post("/books", json={
        "title": "Test Book",
        "author": "Author A",
        "publication_year": 2025,
        "isbn": "TESTISBN001",
        "copies": 1
    }, headers=test_auth_token)
    book_id = book_res.json()["id"]

    reader_res = client.post("/readers", json={
        "name": "Test Reader",
        "email": "reader1@example.com"
    }, headers=test_auth_token)
    reader_id = reader_res.json()["id"]

    res = client.post("/borrow", json={"book_id": book_id, "reader_id": reader_id}, headers=test_auth_token)
    assert res.status_code == 200
    assert res.json()["book_id"] == book_id
    assert res.json()["reader_id"] == reader_id

def test_borrow_book_unavailable(test_auth_token):
    res = client.post("/borrow", json={"book_id": 1, "reader_id": 1}, headers=test_auth_token)
    assert res.status_code == 400
    assert "No copies available" in res.json()["detail"]

def test_borrow_more_than_three_books(test_auth_token):
    reader_res = client.post("/readers", json={
        "name": "Max Borrower",
        "email": "max@example.com"
    }, headers=test_auth_token)
    reader_id = reader_res.json()["id"]

    for i in range(2, 5):
        client.post("/books", json={
            "title": f"Book {i}",
            "author": f"Author {i}",
            "publication_year": 2020 + i,
            "isbn": f"ISBN{i}",
            "copies": 1
        }, headers=test_auth_token)

    for i in range(2, 5):
        res = client.post("/borrow", json={"book_id": i, "reader_id": reader_id}, headers=test_auth_token)
        assert res.status_code == 200

    client.post("/books", json={
        "title": "Book 5",
        "author": "Author 5",
        "publication_year": 2025,
        "isbn": "ISBN5",
        "copies": 1
    }, headers=test_auth_token)

    res = client.post("/borrow", json={"book_id": 5, "reader_id": reader_id}, headers=test_auth_token)
    assert res.status_code == 400
    assert "already borrowed 3 books" in res.json()["detail"]

def test_return_book_success(test_auth_token):
    book_res = client.post("/books", json={
        "title": "Returnable Book",
        "author": "Author Return",
        "publication_year": 2025,
        "isbn": "RETURNBOOK1",
        "copies": 1
    }, headers=test_auth_token)
    book_id = book_res.json()["id"]

    reader_res = client.post("/readers", json={
        "name": "Return Reader",
        "email": "return@example.com"
    }, headers=test_auth_token)
    reader_id = reader_res.json()["id"]

    borrow_res = client.post("/borrow", json={
        "book_id": book_id,
        "reader_id": reader_id
    }, headers=test_auth_token)
    borrow_id = borrow_res.json()["id"]

    return_res = client.post("/return", json={"borrow_id": borrow_id}, headers=test_auth_token)
    assert return_res.status_code == 200
    assert return_res.json()["return_date"] is not None

    book_after = client.get(f"/books/{book_id}", headers=test_auth_token)
    assert book_after.json()["copies"] == 1


def test_return_book_invalid_cases(test_auth_token):
    res = client.post("/return", json={"borrow_id": 999}, headers=test_auth_token)
    assert res.status_code == 404

    book_res = client.post("/books", json={
        "title": "Double Return Book",
        "author": "Author D",
        "publication_year": 2024,
        "isbn": "DBLRETURN",
        "copies": 1
    }, headers=test_auth_token)
    book_id = book_res.json()["id"]

    reader_res = client.post("/readers", json={
        "name": "Double Reader",
        "email": "double@example.com"
    }, headers=test_auth_token)
    reader_id = reader_res.json()["id"]

    borrow_res = client.post("/borrow", json={
        "book_id": book_id,
        "reader_id": reader_id
    }, headers=test_auth_token)
    borrow_id = borrow_res.json()["id"]

    res1 = client.post("/return", json={"borrow_id": borrow_id}, headers=test_auth_token)
    assert res1.status_code == 200

    res2 = client.post("/return", json={"borrow_id": borrow_id}, headers=test_auth_token)
    assert res2.status_code == 404
