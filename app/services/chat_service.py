from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.models import Conversation, Message
from app.schemas.schemas import ConversationCreate, MessageCreate

class ChatService:
    """Service for handling chat-related database operations"""
    
    @staticmethod
    async def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    @staticmethod
    async def create_conversation(db: Session, conversation: ConversationCreate) -> Conversation:
        """Create a new conversation"""
        db_conversation = Conversation(
            title=conversation.title,
            user_id=conversation.user_id
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation
    
    @staticmethod
    async def create_message(db: Session, message: MessageCreate, conversation_id: str) -> Message:
        """Create a new message in a conversation"""
        db_message = Message(
            role=message.role,
            content=message.content,
            conversation_id=conversation_id
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message
    
    @staticmethod
    async def get_conversation_messages(db: Session, conversation_id: str) -> List[Message]:
        """Get all messages in a conversation"""
        return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all()
    
    @staticmethod
    async def format_messages_for_langchain(messages: List[Message]) -> List[Dict[str, Any]]:
        """Format messages for LangChain"""
        return [
            {
                "role": message.role,
                "content": message.content
            }
            for message in messages
        ]
    
    # Non-async versions of the methods for compatibility
    @staticmethod
    def get_conversation_sync(db: Session, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID (sync version)"""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    @staticmethod
    def create_conversation_sync(db: Session, conversation: ConversationCreate) -> Conversation:
        """Create a new conversation (sync version)"""
        db_conversation = Conversation(
            title=conversation.title,
            user_id=conversation.user_id
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation
    
    @staticmethod
    def create_message_sync(db: Session, message: MessageCreate, conversation_id: str) -> Message:
        """Create a new message in a conversation (sync version)"""
        db_message = Message(
            role=message.role,
            content=message.content,
            conversation_id=conversation_id
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message
    
    @staticmethod
    def get_conversation_messages_sync(db: Session, conversation_id: str) -> List[Message]:
        """Get all messages in a conversation (sync version)"""
        return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at).all() 