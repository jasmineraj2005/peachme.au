import os
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain.callbacks.tracers import LangChainTracer
from langchain.callbacks.tracers.langchain import wait_for_all_tracers
from langchain_core.tracers import ConsoleCallbackHandler
from langchain_core.callbacks import CallbackManager
from dotenv import load_dotenv
import uuid
import logging
from pydantic import BaseModel, Field
from langchain_core.pydantic_v1 import BaseModel as LangchainBaseModel
from langchain_core.output_parsers import PydanticOutputParser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "peachme-chat")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"

# Define Pydantic models for structured output
class CriteriaFeedback(LangchainBaseModel):
    score: int = Field(..., description="Rating score from 1-5")
    feedback: str = Field(..., description="Detailed feedback for this criteria")

class PitchEvaluation(LangchainBaseModel):
    stated_problem: CriteriaFeedback = Field(..., description="Evaluation of how well the problem is stated")
    identified_solution: CriteriaFeedback = Field(..., description="Evaluation of the proposed solution")
    target_market: CriteriaFeedback = Field(..., description="Evaluation of the target market analysis")
    competitive_advantage: CriteriaFeedback = Field(..., description="Evaluation of the competitive advantage")
    viability_sustainability: CriteriaFeedback = Field(..., description="Evaluation of business viability and sustainability")
    overall_feedback: str = Field(..., description="Overall feedback on the pitch")

# Default system message
DEFAULT_SYSTEM_MESSAGE = """
You are a hackathon/startup pitch coach.

You are given a pitch transcript from a startup pitch competition.

You need to evaluate the pitch and provide feedback on the following criteria:
1. Stated Problem (Score 1-5): How well is the problem articulated?
2. Identified Solution (Score 1-5): How relevant and effective is the proposed solution?
3. Target Market (Score 1-5): How well is the target market identified and analyzed?
4. Competitive Advantage (Score 1-5): How clear is the competitive advantage?
5. Viability/Sustainability (Score 1-5): How viable and sustainable is the business model?

For each criterion, provide a score (1-5) and detailed feedback.
Also provide an overall feedback summarizing the pitch's strengths and areas for improvement.

YOUR RESPONSE MUST BE IN THE EXACT FORMAT SPECIFIED BY THE OUTPUT PARSER.
"""

# Initialize the OpenAI model
def get_llm(temperature: float = 0.7, model_name: str = "gpt-3.5-turbo", run_id: Optional[str] = None):
    """
    Initialize and return an OpenAI language model with tracing.
    
    Args:
        temperature: Controls randomness. Higher values make output more random,
                    lower values make it more deterministic.
        model_name: The name of the OpenAI model to use.
        run_id: Optional run ID for tracing.
        
    Returns:
        An initialized OpenAI language model.
    """
    callbacks = []
    
    # Add console callback for local debugging
    callbacks.append(ConsoleCallbackHandler())
    
    # Add LangSmith tracer if API key is available
    if LANGCHAIN_API_KEY:
        try:
            tracer = LangChainTracer(
                project_name=LANGCHAIN_PROJECT,
                run_id=run_id
            )
            callbacks.append(tracer)
        except Exception as e:
            logger.error(f"Error initializing LangChain tracer: {str(e)}")
    
    callback_manager = CallbackManager(callbacks)
    
    return ChatOpenAI(
        temperature=temperature,
        model=model_name,
        api_key=OPENAI_API_KEY,
        callbacks=callbacks
    )

# Create a chat prompt template
def get_chat_prompt_template(system_message: Optional[str] = None):
    """
    Create a chat prompt template with an optional system message.
    
    Args:
        system_message: A system message to guide the model's behavior.
        
    Returns:
        A chat prompt template.
    """
    if system_message:
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
    else:
        return ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

# Format message history for LangChain
def format_message_history(messages: List[Dict[str, Any]]):
    """
    Format message history from the database into LangChain message objects.
    
    Args:
        messages: A list of message dictionaries from the database.
        
    Returns:
        A list of LangChain message objects.
    """
    formatted_messages = []
    
    for message in messages:
        if message["role"] == "user":
            formatted_messages.append(HumanMessage(content=message["content"]))
        elif message["role"] == "assistant":
            formatted_messages.append(AIMessage(content=message["content"]))
    
    return formatted_messages

# Generate a response
async def generate_response(
    user_input: str, 
    message_history: Optional[List[Dict[str, Any]]] = None, 
    system_message: Optional[str] = None, 
    user_id: Optional[str] = None, 
    conversation_id: Optional[str] = None,
    use_structured_output: bool = False
) -> str:
    """
    Generate a response using the LangChain chat chain.
    
    Args:
        user_input: The user's input message.
        message_history: A list of previous messages.
        system_message: A system message to guide the model's behavior.
        user_id: The ID of the user for tracing.
        conversation_id: The ID of the conversation for tracing.
        use_structured_output: Whether to use structured output.
        
    Returns:
        The generated response.
    """
    # Default system message if none provided
    if system_message is None:
        system_message = DEFAULT_SYSTEM_MESSAGE
    
    # Initialize message history if none provided
    if message_history is None:
        message_history = []
    
    # Format message history for LangChain
    formatted_history = format_message_history(message_history)
    
    # Generate a run ID for tracing
    run_id = str(uuid.uuid4())
    
    # Add metadata for tracing
    metadata = {
        "conversation_id": conversation_id or "new_conversation",
        "user_id": user_id or "anonymous",
        "message_history_length": len(message_history)
    }
    
    # Create LLM
    llm = get_llm(temperature=0.7, model_name="gpt-4o", run_id=run_id)
    
    # Create prompt
    prompt = get_chat_prompt_template(system_message)
    
    try:
        if use_structured_output:
            # Use Pydantic output parser for structured output
            parser = PydanticOutputParser(pydantic_object=PitchEvaluation)
            
            # Add format instructions to the system message
            format_instructions = parser.get_format_instructions()
            enhanced_system_message = f"{system_message}\n\n{format_instructions}"
            
            # Create prompt with enhanced system message
            prompt = get_chat_prompt_template(enhanced_system_message)
            
            # Create chain with parser
            chain = prompt | llm | parser
            
            # Generate response with metadata
            response = await chain.ainvoke(
                {
                    "input": user_input,
                    "chat_history": formatted_history
                },
                config={"metadata": metadata}
            )
            
            # Format the structured response for display
            formatted_response = format_structured_response(response)
            
            # Wait for tracers to finish
            if LANGCHAIN_API_KEY:
                wait_for_all_tracers()
                
            return formatted_response
        else:
            # Create chain for text output
            chain = prompt | llm | StrOutputParser()
            
            # Generate response with metadata
            response = await chain.ainvoke(
                {
                    "input": user_input,
                    "chat_history": formatted_history
                },
                config={"metadata": metadata}
            )
            
            # Wait for tracers to finish
            if LANGCHAIN_API_KEY:
                wait_for_all_tracers()
                
            return response
    except Exception as e:
        # Log the error
        logger.error(f"Error in generate_response: {str(e)}")
        raise e

def format_structured_response(evaluation: PitchEvaluation) -> str:
    """
    Format the structured pitch evaluation into a readable string.
    
    Args:
        evaluation: The structured pitch evaluation.
        
    Returns:
        A formatted string representation of the evaluation.
    """
    formatted_response = "### Evaluation of the Pitch\n\n"
    
    # Format each criteria
    formatted_response += f"#### 1. Stated Problem\n\n- **Score: {evaluation.stated_problem.score}**\n- **Feedback:** {evaluation.stated_problem.feedback}\n\n"
    formatted_response += f"#### 2. Identified Solution\n\n- **Score: {evaluation.identified_solution.score}**\n- **Feedback:** {evaluation.identified_solution.feedback}\n\n"
    formatted_response += f"#### 3. Target Market\n\n- **Score: {evaluation.target_market.score}**\n- **Feedback:** {evaluation.target_market.feedback}\n\n"
    formatted_response += f"#### 4. Competitive Advantage\n\n- **Score: {evaluation.competitive_advantage.score}**\n- **Feedback:** {evaluation.competitive_advantage.feedback}\n\n"
    formatted_response += f"#### 5. Viability/Sustainability\n\n- **Score: {evaluation.viability_sustainability.score}**\n- **Feedback:** {evaluation.viability_sustainability.feedback}\n\n"
    
    # Add overall feedback
    formatted_response += f"### Overall Feedback\n\n{evaluation.overall_feedback}"
    
    return formatted_response

# Process a chat message (complete flow)
async def process_chat_message(
    db: Session,
    message_content: str,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    use_structured_output: bool = False
) -> Dict[str, Any]:
    """
    Process a chat message and generate a response.
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
    from app.models.models import Conversation, Message
    from app.schemas.schemas import MessageCreate, ConversationCreate
    from app.services.chat_service import ChatService
    
    # Get or create conversation
    if conversation_id:
        conversation = await ChatService.get_conversation(db, conversation_id)
        if not conversation:
            # Instead of raising a 404, create a new conversation
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
        # Generate AI response using LangChain
        ai_response = await generate_response(
            user_input=message_content,
            message_history=message_history[:-1],  # Exclude the last message (current user message)
            system_message=DEFAULT_SYSTEM_MESSAGE,
            user_id=user_id or "anonymous",
            conversation_id=conversation.id,
            use_structured_output=use_structured_output
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