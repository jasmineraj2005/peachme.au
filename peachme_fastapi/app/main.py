from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import chat_router, video_router
from dotenv import load_dotenv


load_dotenv()

app = FastAPI(
    title="PeachMe API",
    description="API for PeachMe chat and video analysis application",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, in production specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(video_router, prefix="/api/video")


@app.get("/")
async def root():
    """Root endpoint that returns API information"""
    return {
        "message": "Welcome to PeachMe API",
        "api_endpoints": {
            "chat": "/api/chat",
            "conversations": "/api/conversations",
            "video": {
                "transcribe": "/api/video/transcribe",
                "analyze": "/api/video/analyze"
            }
        }
    }
