
# Library API

## Overview

This project implements a RESTful API for managing a library system using **FastAPI**, **PostgreSQL**, and **SQLAlchemy**. It allows authenticated librarians to manage books and readers, and to control the borrowing and returning of books.

The system uses:
- **JWT authentication** with `python-jose`
- **Password hashing** with `passlib[bcrypt]`
- **Request/response validation** via `Pydantic`
- **Alembic** for managing database migrations
- **Pytest** for test automation

---

## Setup Instructions

1. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   Enter desired values into the `.env` file:
   ```
    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/library_db
    SECRET_KEY = some_secret_key
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    ALGORITHM = "HS256"
   ```
   Since the same application signs and verifies token, symmetric signing algorithm "HS256" is used.

3. **Apply database migrations**:
   ```
   alembic upgrade head
   ```

4. **Run the application**:
   ```
   uvicorn app.main:app --reload
   ```

5. **Register a librarian (user)**:
   Send a `POST` request to `/auth/register` with:
   ```json
   {
     "email": "admin@example.com",
     "password": "securepassword"
   }
   ```

   The response will include an access token for authenticated routes The token is used for CRUD operations on books and readers, as well as book borrow and return operations.

## Project Structure

```
app/
├── main.py                # FastAPI app and route registration
├── models/                # SQLAlchemy models
├── schemas/               # Pydantic schemas
├── routes/                # API endpoints
├── dependencies/          # Auth utilities
├── core/                  # Settings/config
tests/                     # Pytest test cases
alembic/                   # Migration scripts
```

## Database Design Decisions

Defined in `models/models.py` using SQLAlchemy ORM:

- `User`: stores librarian credentials (`email`, `hashed_password`)
- `Book`: contains `title`, `author`, `publication_year`, `isbn`, `copies`, `description`
- `Reader`: includes `name`, `email`, and is not an authenticated entity
- `BorrowedBook`: represents borrow records with `book_id`, `reader_id`, `borrow_date`, `return_date`. Uniqueness is enforced via:
  ```python
  UniqueConstraint('book_id', 'reader_id', 'return_date')
  ```

Migrations are managed with **Alembic**:
- `cd9e9bad3263_create_tables.py`: initial tables
- `43053869f21c_add_description_field_to_books.py`: adds optional `description` to `Book`

---

## Business Logic Implementation

### 1. Available Copies
Books can only be borrowed if `copies > 0`. Before borrowing, we ensure:
```python
if book.copies <= 0:
    raise HTTPException(...)
```

### 2. Max Borrow Limit
A reader cannot borrow more than 3 books at the same time. This is enforced by counting active borrows (where `return_date IS NULL`).
```python
active_borrows = db.query(BorrowedBook).filter(..., return_date == None).count()
```

### 3. Valid Return
Books can only be returned if they are currently borrowed and not yet returned. Upon return, `return_date` is set and `copies` is incremented.
```python
borrow = db.query(BorrowedBook).filter(
            BorrowedBook.book_id == request.book_id,
            BorrowedBook.reader_id == request.reader_id,
            BorrowedBook.return_date == None
        ).first()
if not borrow or borrow.return_date is not None:
    raise HTTPException(...)
```

### Business Logic Challenges Reflection
- The challenge of tracking available books was easily solvable by adding the `copies` field to SQLAlchemy `Book` class.
- To be able to quickly access all information about borrowed books, a `BorrowedBook` table was created. By relating it to both an entry in the `Book` and the `Reader` table, we can quickly and concisely find information about a particular reader's or book's borrows. This enabled short and clean solution to Business Logic 2 and 3.

---

## Authentication Design

Implemented in `routes/auth.py` using:

- **JWT creation**: via `jose.jwt.encode()`
- **Password hashing**: via `passlib.context.CryptContext`
- **Login & Registration** return access tokens

### Route Protection
Authentication is enforced using:
```python
user = Depends(get_current_user)
```

Defined in `dependencies/dependencies.py`, `get_current_user()`:
- Parses and verifies the JWT from the `Authorization` header
- Decodes the token using `SECRET_KEY`
- Loads the `User` from the database
- Raises `401 Unauthorized` if token is missing/invalid

This design makes it easy to secure any route by injecting the dependency:
```python
@router.post("/books", ...)
def create_book(..., user=Depends(get_current_user)):
```

The only unprotected endpoint is `list_books` in `app/routes/books.py`. Unlike other endpoints, which allow manipulating data, `list_books` showcases the entire available book catalogue to allow unregistered users to evaluate the books selection.

---

## Authentication Libraries and Why They Were Used

### 1. `python-jose`
This library is used to **encode and decode JWT tokens**. It allows us to:
- Sign access tokens securely with a secret key and algorithm (e.g., HS256)
- Include custom claims like `sub` (user email) and `exp` (expiration time)
- Verify token validity during protected route access

JWTs are stateless and eliminate the need for session storage, making the API scalable.

### 2. `passlib[bcrypt]`
Used to **securely hash and verify user passwords**. Instead of storing plaintext passwords, the program:
- On registration: passwords are hashed using `pwd_context.hash(password)`
- On login: incoming password is verified using `pwd_context.verify(plain, hashed)`

`bcrypt` is a strong hashing algorithm widely adopted for secure password storage.

### 3. `FastAPI Depends()`
The `Depends(get_current_user)` mechanism enforces authentication on protected routes. It:
- Extracts the JWT from the request header
- Decodes and validates the token
- Ensures the user exists in the database
- Injects the user into the route handler if valid

This makes route protection declarative and consistent throughout the API.

---

## Alembic Migrations

1. **Initial Migration**: Creates tables for `users`, `books`, `readers`, `borrowed_books`
2. **Second Migration**: Adds optional `description` field to `books` table

## Tests

Implemented using **Pytest** in `tests/`:

- Borrow/return scenarios including business logic violations
- JWT protection checks (access with and without tokens)
- CRUD operations for books

Run tests:
```bash
pytest
```

---

## Suggested Feature: Due Dates and Overdue Tracking

Add a `due_date` field to `BorrowedBook`, calculated at borrow time (e.g., 14 days after `borrow_date`). Use it to notify readers of upcoming or overdue deadline, implement overdue checks and notify librarians of violations. This would require a background job or periodic scan to flag overdue entries. Notifications can be distributed via email (librarian and reader emails are already stored in the database). Gmail API could be used to log into account and send out notifications.
