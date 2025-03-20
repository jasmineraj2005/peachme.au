from fastapi import APIRouter, HTTPException, status, UploadFile, File
from typing import List, Dict
import logging
from fastapi.responses import StreamingResponse
import os
from pathlib import Path

from app.schemas.schemas import (
    ChatRequest, 
    ChatResponse, 
    TranscriptionResponse,
    FeedbackResponse,
    ContextExtractionResponse,
    EnhancedFeedbackResponse,
    MarketResearchResponse,
    CompetitorResponse,
    MarketSizeResponse,
    MarketTrendResponse
)
from app.services.speech_to_text import get_transcript
from app.core.agent_utils import analyze_pitch, extract_pitch_context, conduct_market_research, PitchContextExtraction

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

@video_router.post("/analyze", response_model=EnhancedFeedbackResponse)
async def analyze_transcript(
    request: ChatRequest,
):
    """
    Analyze a transcript and get structured feedback with context extraction.
    The transcript should be provided in the message field of the request.
    
    This endpoint performs two steps:
    1. Extract context (industry, verticals, problem) from the transcript
    2. Analyze the pitch quality and provide structured feedback
    """
    try:
        # First, extract context from the transcript
        context_extraction = await extract_pitch_context(pitch_content=request.message)
        
        # Log the extracted context
        logger.info(f"Extracted context: Industry={context_extraction.industry}, "
                   f"Verticals={context_extraction.verticals}, "
                   f"Problem={context_extraction.problem}")
        
        # Then, analyze the pitch with the extracted context
        result = await analyze_pitch(
            pitch_content=request.message,
            context_extraction=context_extraction
        )

        # Return both the analysis results and the extracted context
        return EnhancedFeedbackResponse(
            clarity=result.clarity,
            clarity_feedback=result.clarity_feedback,
            content=result.content,
            content_feedback=result.content_feedback,
            structure=result.structure,
            structure_feedback=result.structure_feedback,
            delivery=result.delivery,
            delivery_feedback=result.delivery_feedback,
            feedback=result.feedback,
            context=ContextExtractionResponse(
                industry=context_extraction.industry,
                verticals=context_extraction.verticals,
                problem=context_extraction.problem,
                summary=context_extraction.summary
            )
        )

    except Exception as e:
        logger.error(f"Error in analyze_transcript: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@video_router.post("/market-research", response_model=MarketResearchResponse)
async def research_market(
    request: ChatRequest,
):
    """
    Conduct market research based on pitch context.
    This endpoint expects a message containing the pitch context in JSON format:
    {
        "industry": "string",
        "verticals": ["string"],
        "problem": "string",
        "summary": "string"
    }
    """
    logger.info(f"Market research endpoint called with message: {request.message[:100]}...")
    
    try:
        # Parse the context from the request message
        try:
            import json
            context_data = json.loads(request.message)
            
            # Log parsed data
            logger.info(f"Successfully parsed JSON context: {context_data}")
            
            # Create PitchContextExtraction object
            context_extraction = PitchContextExtraction(
                industry=context_data.get("industry", ""),
                verticals=context_data.get("verticals", []),
                problem=context_data.get("problem", ""),
                summary=context_data.get("summary", "")
            )
        except json.JSONDecodeError as e:
            # If not valid JSON, try to use it directly as an industry name
            logger.warning(f"Received non-JSON input for market research: {e}")
            context_extraction = PitchContextExtraction(
                industry=request.message,
                verticals=[],
                problem="",
                summary=""
            )
        
        # Log the context
        logger.info(f"Conducting market research for: Industry={context_extraction.industry}, "
                   f"Verticals={context_extraction.verticals}")
        
        # Conduct market research using the agent
        research_results = await conduct_market_research(context_extraction)
        
        # Add logging to help with debugging
        logger.info(f"Research results type: {type(research_results).__name__}")
        
        # Convert to response schema - now handling dictionary access with get()
        competitors = [
            CompetitorResponse(
                name=comp.get("name", ""),
                description=comp.get("description", ""),
                url=comp.get("url")
            ) for comp in research_results.get("competitors", [])
        ]
        
        market_size = MarketSizeResponse(
            overall=research_results.get("market_size", {}).get("overall", "Unknown"),
            growth=research_results.get("market_size", {}).get("growth"),
            projection=research_results.get("market_size", {}).get("projection")
        )
        
        trends = [
            MarketTrendResponse(
                title=trend.get("title", ""),
                description=trend.get("description", "")
            ) for trend in research_results.get("trends", [])
        ]
        
        return MarketResearchResponse(
            competitors=competitors,
            market_size=market_size,
            trends=trends,
            summary=research_results.get("summary", "No summary available")
        )

    except Exception as e:
        logger.error(f"Error in research_market: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@video_router.get("/test-connection")
async def test_connection():
    """
    Simple endpoint to test API connectivity
    """
    logger.info("Test connection endpoint called")
    return {"status": "ok", "message": "API is working"} 