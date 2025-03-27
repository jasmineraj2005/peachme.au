from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.api.routes import video_router

# Load environment variables
load_dotenv()

# Get CORS origins from environment variable
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# For development, ensure all localhost origins are allowed
CORS_ORIGINS.extend([
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8001",  # The current FastAPI port
    "http://127.0.0.1:8001"   # Alternative localhost notation
])

# Log the allowed origins for debugging
print(f"CORS allowed origins: {CORS_ORIGINS}")

# Create FastAPI app
app = FastAPI(
    title="PeachMe API",
    description="API for PeachMe video transcription and analysis",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(video_router, prefix="/api/video")

@app.get("/")
async def root():
    """Root endpoint that returns API information"""
    return {
        "message": "Welcome to PeachMe API",
        "api_endpoints": {
            "video": {
                "transcribe": "/api/video/transcribe",
                "analyze": "/api/video/analyze"
            }
        }
    }
