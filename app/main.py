from fastapi import FastAPI
from app.routes import auth, books, readers

app = FastAPI()

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(books.router, tags=["books"])
app.include_router(readers.router, tags=["readers"])