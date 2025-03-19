from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from agents import Agent, Runner, trace, guardrails
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class PitchContext:
    """Context for pitch-related operations"""
    conversation_history: List[Dict[str, Any]]
    pitch_content: Optional[str] = None

    def get_conversation_messages(self) -> List[Dict[str, str]]:
        """Format conversation history into messages"""
        return [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in self.conversation_history
        ]

class PitchEvaluation(BaseModel):
    """Structured output for pitch evaluation"""
    clarity: int = Field(description="Rating from 1-5 for clarity of presentation", ge=1, le=5)
    content: int = Field(description="Rating from 1-5 for content quality", ge=1, le=5)
    structure: int = Field(description="Rating from 1-5 for pitch structure", ge=1, le=5)
    delivery: int = Field(description="Rating from 1-5 for delivery style", ge=1, le=5)
    feedback: str = Field(description="Detailed feedback and suggestions", min_length=50)

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "clarity": 4,
                    "content": 3,
                    "structure": 4,
                    "delivery": 3,
                    "feedback": "Your pitch demonstrates good clarity and structure. The main points are well-organized and easy to follow. However, the content could be more compelling with specific examples and data points. The delivery could be improved by varying your pace and adding more emphasis on key points."
                }
            ]
        }

# Define guardrails for pitch analysis
@guardrails.validate_output
def validate_pitch_evaluation(eval: PitchEvaluation) -> bool:
    """Validate pitch evaluation output"""
    # Ensure all ratings are between 1 and 5
    ratings_valid = all(1 <= rating <= 5 for rating in [
        eval.clarity, eval.content, eval.structure, eval.delivery
    ])
    
    # Ensure feedback is substantial
    feedback_valid = len(eval.feedback.split()) >= 20
    
    return ratings_valid and feedback_valid

# Create agents for different purposes
pitch_analysis_agent = Agent[PitchContext](
    name="pitch_analysis_agent",
    instructions="""You are an expert pitch coach. Analyze pitch presentations and provide structured feedback.
    Focus on clarity, content quality, structure, and delivery style.
    Be specific in your feedback and provide actionable suggestions for improvement.
    
    For each criterion:
    - Clarity (1-5): How clear and understandable is the pitch?
    - Content (1-5): How compelling and valuable is the content?
    - Structure (1-5): How well-organized is the presentation?
    - Delivery (1-5): How effective is the delivery style?
    
    Provide detailed feedback with specific examples and suggestions.""",
    output_type=PitchEvaluation,
    guardrails=[validate_pitch_evaluation],
)

chat_agent = Agent[PitchContext](
    name="chat_agent",
    instructions="""You are a helpful AI assistant specializing in startup pitches and presentations.
    Provide clear, constructive advice and engage in meaningful dialogue about pitch improvement.
    Be encouraging while maintaining honesty in your feedback.
    
    Consider:
    1. The user's specific questions or concerns
    2. The conversation history for context
    3. Previous feedback and suggestions
    4. Areas for improvement
    
    Maintain a supportive and professional tone throughout the conversation."""
)

def create_pitch_context(
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    pitch_content: Optional[str] = None
) -> PitchContext:
    """
    Create a pitch context with conversation history and pitch content.
    
    Args:
        conversation_history: Optional list of previous messages
        pitch_content: Optional pitch content to analyze
        
    Returns:
        PitchContext object with conversation history and pitch content
    """
    return PitchContext(
        conversation_history=conversation_history or [],
        pitch_content=pitch_content
    )

async def analyze_pitch(
    pitch_content: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> PitchEvaluation:
    """
    Analyze a pitch using the pitch analysis agent.
    
    Args:
        pitch_content: The pitch text to analyze
        conversation_history: Optional list of previous messages
        
    Returns:
        PitchEvaluation object containing structured feedback
    """
    with trace("Pitch Analysis") as current_trace:
        # Create context with conversation history and pitch content
        context = create_pitch_context(
            conversation_history=conversation_history,
            pitch_content=pitch_content
        )
            
        # Run the analysis with context and tracing
        result = await Runner.run(
            pitch_analysis_agent,
            pitch_content,
            context=context,
            trace=current_trace
        )
        
        return result.final_output

async def chat_response(
    user_input: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Generate a chat response using the chat agent.
    
    Args:
        user_input: The user's message
        conversation_history: Optional list of previous messages
        
    Returns:
        String response from the agent
    """
    with trace("Chat Response") as current_trace:
        # Create context with conversation history
        context = create_pitch_context(
            conversation_history=conversation_history
        )
            
        # Generate response with context and tracing
        result = await Runner.run(
            chat_agent,
            user_input,
            context=context,
            trace=current_trace
        )
        
        return result.final_output 