from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Message schemas


class MessageBase(BaseModel):
    """Base schema for message data"""
    role: str
    content: str


class MessageCreate(MessageBase):
    """Schema for creating a new message"""
    pass


class Message(MessageBase):
    """Schema for message response"""
    id: str
    conversation_id: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

# Conversation schemas


class ConversationBase(BaseModel):
    """Base schema for conversation data"""
    title: str


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation"""
    user_id: Optional[str] = None


class Conversation(ConversationBase):
    """Schema for conversation response"""
    id: str
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = []

    model_config = {
        "from_attributes": True
    }

# Chat request schema


class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str

# Chat response schema


class ChatResponse(BaseModel):
    """Schema for chat response"""
    response: str

# Conversation messages response schema


class ConversationMessagesResponse(BaseModel):
    """Schema for conversation messages response"""
    messages: List[Message] = Field(description="List of messages in the conversation")
    conversation_id: str = Field(description="The conversation ID")

# Video transcription response schemas
class TranscriptionResponse(BaseModel):
    """Schema for video transcription response"""
    transcript: str

class FeedbackResponse(BaseModel):
    """Schema for feedback response"""
    clarity: int = Field(description="Rating from 1-5 for clarity of presentation")
    clarity_feedback: str = Field(description="Detailed feedback about clarity")
    content: int = Field(description="Rating from 1-5 for content quality")
    content_feedback: str = Field(description="Detailed feedback about content")
    structure: int = Field(description="Rating from 1-5 for pitch structure")
    structure_feedback: str = Field(description="Detailed feedback about structure")
    delivery: int = Field(description="Rating from 1-5 for delivery style")
    delivery_feedback: str = Field(description="Detailed feedback about delivery")
    feedback: str = Field(description="Overall feedback and suggestions")
