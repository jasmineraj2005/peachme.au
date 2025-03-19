from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import logging
from fastapi.responses import StreamingResponse
import os
from pathlib import Path

from app.db.database import get_db
from app.models.models import Conversation, Message
from app.schemas.schemas import (
    ChatRequest, 
    ChatResponse, 
    ConversationMessagesResponse,
    MessageCreate,
    ConversationCreate,
    TranscriptionResponse,
    FeedbackResponse
)
from app.services.chat_service import ChatService
from app.core.chat_processor import process_chat_message
from app.services.speech_to_text import get_transcript

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create routers
chat_router = APIRouter(tags=["chat"])
video_router = APIRouter(tags=["video"])

@chat_router.post("/chat", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message to the chatbot and get a response.
    
    If conversation_id is provided, the message will be added to that conversation.
    If the conversation_id is not found, a new conversation will be created.
    Otherwise, a new conversation will be created.
    """
    try:
        # Process the chat message using the process_chat_message function from langchain_utils
        result = await process_chat_message(
            db=db,
            message_content=request.message,
            conversation_id=request.conversation_id,
            user_id=None  # For now, all users are anonymous
        )
        
        # Return the response
        return ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"]
        )
    except Exception as e:
        logger.error(f"Error in chat_message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@chat_router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message to the chatbot and get a streaming response.
    
    This endpoint returns a streaming response with chunks of the AI's reply
    as they are generated, enabling real-time UI updates.
    """
    async def event_generator():
        try:
            async for chunk in stream_chat_response(
                db=db,
                message_content=request.message,
                conversation_id=request.conversation_id,
                user_id=None  # For now, all users are anonymous
            ):
                # Format each chunk as a server-sent event
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"Error in stream_chat: {str(e)}")
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@chat_router.post("/chat/structured", response_model=ChatResponse)
async def structured_chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message to the chatbot and get a structured response.
    
    This endpoint uses the Pydantic output parser to provide
    a structured analysis of pitch content with scores and detailed feedback.
    """
    try:
        # Process the chat message with structured output
        result = await process_chat_message(
            db=db,
            message_content=request.message,
            conversation_id=request.conversation_id,
            user_id=None,  # For now, all users are anonymous
            use_structured_output=True
        )
        
        # Return the response
        return ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"]
        )
    except Exception as e:
        logger.error(f"Error in structured_chat_message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@chat_router.get("/conversations/{conversation_id}", response_model=ConversationMessagesResponse)
async def get_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all messages in a conversation.
    """
    try:
        conversation = await ChatService.get_conversation(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        messages = await ChatService.get_conversation_messages(db, conversation_id)
        
        return ConversationMessagesResponse(
            messages=messages,
            conversation_id=conversation_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_conversation_messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@video_router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_video(
    video: UploadFile = File(...),
    save_to_conversation: bool = False,
    db: Session = Depends(get_db)
):
    """
    Upload a video file and get its transcript.
    Optionally save the transcript to a new conversation.
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

        # Get transcript
        transcript = get_transcript(str(video_path))
        
        if isinstance(transcript, str) and transcript.startswith("Error:"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=transcript
            )

        # Optionally save to conversation
        conversation_id = None
        if save_to_conversation:
            result = await process_chat_message(
                db=db,
                message_content=transcript,
                conversation_id=None,
                user_id=None,
                save_only=True  # Only save, don't process
            )
            conversation_id = result["conversation_id"]

        return TranscriptionResponse(
            transcript=transcript,
            conversation_id=conversation_id
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
    db: Session = Depends(get_db)
):
    """
    Analyze a transcript and get structured feedback.
    The transcript should be provided in the message field of the request.
    """
    try:
        result = await process_chat_message(
            db=db,
            message_content=request.message,
            conversation_id=request.conversation_id,
            user_id=None,
            use_structured_output=True
        )

        return FeedbackResponse(
            feedback=result["response"],
            conversation_id=result["conversation_id"]
        )

    except Exception as e:
        logger.error(f"Error in analyze_transcript: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        ) 