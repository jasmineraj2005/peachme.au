from fastapi import APIRouter, HTTPException, status, UploadFile, File
from typing import List
import logging
from fastapi.responses import StreamingResponse
import os
from pathlib import Path

from app.schemas.schemas import (
    ChatRequest, 
    ChatResponse, 
    TranscriptionResponse,
    FeedbackResponse
)
from app.services.speech_to_text import get_transcript
from app.core.agent_utils import analyze_pitch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create routers
video_router = APIRouter(tags=["video"])

@video_router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_video(
    video: UploadFile = File(...),
):
    """
    Upload a video file and get its transcript using OpenAI's Whisper API.
    """
    try:
        # Create media directory if it doesn't exist
        media_dir = Path("media")
        media_dir.mkdir(exist_ok=True)
        
        # Save uploaded video
        video_path = media_dir / video.filename
        with open(video_path, "wb") as f:
            content = await video.read()
            f.write(content)

        # Get transcript from OpenAI API
        transcript = get_transcript(str(video_path))
        
        if isinstance(transcript, str) and transcript.startswith("Error:"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=transcript
            )

        return TranscriptionResponse(
            transcript=transcript
        )

    except Exception as e:
        logger.error(f"Error in transcribe_video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@video_router.post("/analyze", response_model=FeedbackResponse)
async def analyze_transcript(
    request: ChatRequest,
):
    """
    Analyze a transcript and get structured feedback.
    The transcript should be provided in the message field of the request.
    """
    try:
        # Call the existing analyze_pitch function
        result = await analyze_pitch(pitch_content=request.message)

        return FeedbackResponse(
            clarity=result.clarity,
            clarity_feedback=result.clarity_feedback,
            content=result.content,
            content_feedback=result.content_feedback,
            structure=result.structure,
            structure_feedback=result.structure_feedback,
            delivery=result.delivery,
            delivery_feedback=result.delivery_feedback,
            feedback=result.feedback
        )

    except Exception as e:
        logger.error(f"Error in analyze_transcript: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        ) 