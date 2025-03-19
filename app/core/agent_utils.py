from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from agents import Agent, Runner, trace
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
    clarity: int = Field(description="Rating from 1-5 for clarity of presentation")
    clarity_feedback: str = Field(description="Detailed feedback about clarity")
    content: int = Field(description="Rating from 1-5 for content quality")
    content_feedback: str = Field(description="Detailed feedback about content")
    structure: int = Field(description="Rating from 1-5 for pitch structure")
    structure_feedback: str = Field(description="Detailed feedback about structure")
    delivery: int = Field(description="Rating from 1-5 for delivery style")
    delivery_feedback: str = Field(description="Detailed feedback about delivery")
    feedback: str = Field(description="Overall feedback and suggestions")

# Create agents for different purposes
pitch_analysis_agent = Agent[PitchContext](
    name="pitch_analysis_agent",
    instructions="""You are an expert pitch coach. Analyze pitch presentations and provide structured feedback.
    Focus on clarity, content quality, structure, and delivery style.
    Be specific in your feedback and provide actionable suggestions for improvement.
    
    For each criterion, provide a rating and detailed feedback:
    
    - Clarity (1-5): How clear and understandable is the pitch?
      - Provide specific feedback about clarity, focusing on language choices, explanation quality, and how well ideas are communicated.
    
    - Content (1-5): How compelling and valuable is the content?
      - Provide specific feedback about content value, focusing on uniqueness, evidence/data included, value proposition, and market relevance.
    
    - Structure (1-5): How well-organized is the presentation?
      - Provide specific feedback about structure, focusing on logical flow, organization, transitions between topics, and overall narrative arc.
    
    - Delivery (1-5): How effective is the delivery style?
      - Provide specific feedback about delivery, focusing on pacing, emphasis, confidence, engagement, and overall presentation style.
    
    Also provide overall feedback summarizing key strengths and areas for improvement across all categories.
    
    Make your feedback constructive, specific, and actionable with clear examples from the pitch.""",
    output_type=PitchEvaluation,
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
            pitch_content
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
            user_input
        )
        
        return result.final_output 