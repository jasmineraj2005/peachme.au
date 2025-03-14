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

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

# Chat request schema


class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str = Field(..., description="The user's message")
    conversation_id: Optional[str] = Field(
        None, description="The conversation ID (if continuing a conversation)")

# Chat response schema


class ChatResponse(BaseModel):
    """Schema for chat response"""
    response: str = Field(..., description="The assistant's response")
    conversation_id: str = Field(..., description="The conversation ID")

# Conversation messages response schema


class ConversationMessagesResponse(BaseModel):
    """Schema for conversation messages response"""
    messages: List[Message] = Field(...,
                                    description="List of messages in the conversation")
    conversation_id: str = Field(..., description="The conversation ID")
