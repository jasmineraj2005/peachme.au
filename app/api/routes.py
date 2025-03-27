from fastapi import APIRouter, HTTPException, status, UploadFile, File
from typing import List, Dict, Any
import logging
from fastapi.responses import StreamingResponse, JSONResponse
import os
from pathlib import Path
import datetime

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
from app.core.agent_utils import analyze_pitch, extract_pitch_context, conduct_market_research, generate_pitch_deck_content, PitchContextExtraction, PitchEvaluation, PitchDeckResponse

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

@video_router.post("/pitch-deck-content")
async def generate_deck_content(
    request: ChatRequest,
):
    """
    Generate content for pitch deck slides based on context from previous analyses.
    This endpoint expects a message containing the pitch context in JSON format.
    """
    # CRITICAL DEBUG LOGGING - Log every request
    logger.info(f"===== PITCH DECK CONTENT ENDPOINT CALLED =====")
    logger.info(f"Request ID: {id(request)} - Time: {datetime.datetime.now().isoformat()}")
    logger.info(f"Request headers available: {request.headers if hasattr(request, 'headers') else 'No headers'}")
    
    try:
        # Parse the context from the request message
        import json
        logger.info(f"Request received: {request}")
        logger.info(f"Request message preview (first 200 chars): {request.message[:200]}")
        
        try:
            data = json.loads(request.message)
            logger.info(f"Successfully parsed JSON with keys: {', '.join(data.keys())}")
        except json.JSONDecodeError as je:
            logger.error(f"JSON decode error: {str(je)}")
            logger.error(f"Raw message: {request.message[:200]}...")
            
            # Return a more detailed error for debugging
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid JSON format in message field: {str(je)}"}
            )
        
        # Extract the necessary context components
        context = data.get("context", {})
        if not context:
            logger.warning("No context found in request")
            
        logger.info(f"Context data: {context}")
        
        context_extraction = PitchContextExtraction(
            industry=context.get("industry", ""),
            verticals=context.get("verticals", []),
            problem=context.get("problem", ""),
            summary=context.get("summary", "")
        )
        logger.info(f"Created PitchContextExtraction with industry={context_extraction.industry}")
        
        # Get market research if available
        market_research = data.get("market_research", None)
        logger.info(f"Market research available: {market_research is not None}")
        if market_research:
            logger.info(f"Market research keys: {', '.join(market_research.keys()) if isinstance(market_research, dict) else 'not a dict'}")
        
        # Get pitch evaluation if available
        pitch_evaluation_data = data.get("evaluation", None)
        logger.info(f"Pitch evaluation available: {pitch_evaluation_data is not None}")
        
        pitch_evaluation = None
        if pitch_evaluation_data:
            pitch_evaluation = PitchEvaluation(
                clarity=pitch_evaluation_data.get("clarity", 3),
                clarity_feedback=pitch_evaluation_data.get("clarity_feedback", ""),
                content=pitch_evaluation_data.get("content", 3),
                content_feedback=pitch_evaluation_data.get("content_feedback", ""),
                structure=pitch_evaluation_data.get("structure", 3),
                structure_feedback=pitch_evaluation_data.get("structure_feedback", ""),
                delivery=pitch_evaluation_data.get("delivery", 3),
                delivery_feedback=pitch_evaluation_data.get("delivery_feedback", ""),
                feedback=pitch_evaluation_data.get("feedback", "")
            )
            logger.info(f"Created PitchEvaluation with clarity={pitch_evaluation.clarity}, content={pitch_evaluation.content}")
        
        # Generate pitch deck content
        logger.info("Calling generate_pitch_deck_content function")
        
        # Call the actual agent
        pitch_deck_response = await generate_pitch_deck_content(
            context_extraction=context_extraction,
            market_research=market_research,
            pitch_evaluation=pitch_evaluation
        )
        
        # Convert the Pydantic model to a dictionary for the JSON response
        logger.info(f"Generated pitch deck response - Overview length: {len(pitch_deck_response.overview)}")
        logger.info(f"JSX code length: {len(pitch_deck_response.jsx_code)}")
        
        # Return the model as a JSON response
        return JSONResponse(content=pitch_deck_response.dict())
        
    except Exception as e:
        logger.error(f"Error in generate_deck_content: {str(e)}")
        logger.exception("Full exception details:")
        return JSONResponse(
            status_code=500,
            content={"error": f"An error occurred: {str(e)}"}
        )

@video_router.get("/test-connection")
async def test_connection():
    """
    Simple endpoint to test API connectivity
    """
    logger.info("Test connection endpoint called")
    return {"status": "ok", "message": "API is working"} 