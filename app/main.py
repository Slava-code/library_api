from fastapi import FastAPI
from app.routes import auth

app = FastAPI()

# Include routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])