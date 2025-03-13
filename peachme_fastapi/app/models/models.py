from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.database import Base

def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())

class Conversation(Base):
    """Conversation model for storing chat conversations"""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    title = Column(String, index=True)
    user_id = Column(String, index=True, nullable=True)  # Can be null for anonymous users
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship with messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title}, user_id={self.user_id})>"

class Message(Base):
    """Message model for storing chat messages"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), index=True)
    role = Column(String, index=True)  # 'user' or 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship with conversation
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>" 