from fastapi import FastAPI
from app.routes import auth, books, readers, borrow

app = FastAPI()

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(readers.router, prefix="/readers", tags=["Readers"])
app.include_router(borrow.router, prefix="/borrow", tags=["Borrowing"])