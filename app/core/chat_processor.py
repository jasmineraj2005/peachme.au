from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from app.models.models import Conversation, Message
from app.schemas.schemas import MessageCreate, ConversationCreate
from app.services.chat_service import ChatService
from app.core.agent_utils import chat_response, analyze_pitch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_chat_message(
    db: Session,
    message_content: str,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    use_structured_output: bool = False
) -> Dict[str, Any]:
    """
    Process a chat message and generate a response using OpenAI Agents.
    This function handles the entire flow from database operations to AI response generation.
    
    Args:
        db: Database session
        message_content: The user's message
        conversation_id: Optional conversation ID
        user_id: Optional user ID
        use_structured_output: Whether to use structured output
        
    Returns:
        Dictionary containing the AI response and conversation ID
    """
    # Get or create conversation
    if conversation_id:
        conversation = await ChatService.get_conversation(db, conversation_id)
        if not conversation:
            # Create a new conversation if not found
            logger.info(f"Conversation {conversation_id} not found, creating a new one")
            title = message_content[:30] + "..." if len(message_content) > 30 else message_content
            conversation = await ChatService.create_conversation(
                db, 
                ConversationCreate(title=title, user_id=user_id)
            )
    else:
        # Create a new conversation with a default title
        title = message_content[:30] + "..." if len(message_content) > 30 else message_content
        conversation = await ChatService.create_conversation(
            db, 
            ConversationCreate(title=title, user_id=user_id)
        )
    
    # Save user message
    user_message = await ChatService.create_message(
        db,
        MessageCreate(role="user", content=message_content),
        conversation.id
    )
    
    # Get conversation history
    messages = await ChatService.get_conversation_messages(db, conversation.id)
    message_history = await ChatService.format_messages_for_langchain(messages)
    
    try:
        # Generate AI response using OpenAI Agents
        if use_structured_output:
            # Use pitch analysis agent for structured output
            analysis_result = await analyze_pitch(
                pitch_content=message_content,
                conversation_history=message_history[:-1]  # Exclude the last message
            )
            # Format the structured response
            ai_response = f"""Pitch Analysis Results:
Clarity: {analysis_result.clarity}/5
Content: {analysis_result.content}/5
Structure: {analysis_result.structure}/5
Delivery: {analysis_result.delivery}/5

Detailed Feedback:
{analysis_result.feedback}"""
        else:
            # Use chat agent for regular responses
            ai_response = await chat_response(
                user_input=message_content,
                conversation_history=message_history[:-1]  # Exclude the last message
            )
        
        logger.info(f"Generated response for conversation {conversation.id}")
    except Exception as e:
        # Log the error
        logger.error(f"Error generating response: {str(e)}")
        
        # Fallback response
        ai_response = "I'm sorry, I encountered an error processing your request. Please try again later."
    
    # Save AI message
    ai_message = await ChatService.create_message(
        db,
        MessageCreate(role="assistant", content=ai_response),
        conversation.id
    )
    
    return {
        "response": ai_response,
        "conversation_id": conversation.id,
        "structured": use_structured_output
    } 