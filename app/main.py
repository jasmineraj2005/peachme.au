from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.api.routes import video_router

# Load environment variables
load_dotenv()

# Get CORS origins from environment variable
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Create FastAPI app
app = FastAPI(
    title="PeachMe API",
    description="API for PeachMe video transcription and analysis",
    version="1.0.0"
)

# Add CORS middleware
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
