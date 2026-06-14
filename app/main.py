"""
Main entrypoint for the Anernan FastAPI application.
Initialises the application, sets up CORS middleware, creates database
tables, and registers routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, documents

# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Anernan API",
    description="Self-hosted, AI-augmented Idea Vault backend API.",
    version="1.0.0"
)

# Configure CORS middleware to permit requests from frontend dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to specific origins in a production configuration
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(documents.router)

@app.get("/")
def read_root():
    """
    Root status endpoint to verify the API server is online.
    """
    return {
        "status": "online",
        "message": "Welcome to Anernan API"
    }

