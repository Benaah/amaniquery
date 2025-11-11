"""
Database Models for Chat Sessions, Messages, and Feedback
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from pydantic import BaseModel

Base = declarative_base()

class ChatSession(Base):
    """Chat session model"""
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)  # For future user authentication
    title = Column(String, nullable=True)  # Auto-generated from first message
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Message metadata
    token_count = Column(Integer, nullable=True)
    model_used = Column(String, nullable=True)
    sources = Column(JSON, nullable=True)  # Store sources as JSON

    # Feedback
    feedback_type = Column(String, nullable=True)  # "like", "dislike", or None
    feedback_comment = Column(Text, nullable=True)
    feedback_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class UserFeedback(Base):
    """General user feedback model"""
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=True)
    message_id = Column(String, ForeignKey("chat_messages.id"), nullable=True)
    feedback_type = Column(String, nullable=False)  # "like", "dislike", "share", "copy"
    content = Column(Text, nullable=True)  # Additional feedback content
    metadata = Column(JSON, nullable=True)  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic models for API
class ChatSessionCreate(BaseModel):
    title: Optional[str] = None
    user_id: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: int = 0

class ChatMessageCreate(BaseModel):
    content: str
    role: str = "user"

class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime
    token_count: Optional[int]
    model_used: Optional[str]
    sources: Optional[List[dict]]
    feedback_type: Optional[str]

class FeedbackCreate(BaseModel):
    message_id: str
    feedback_type: str  # "like", "dislike", "share", "copy"
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    message_id: str
    feedback_type: str
    comment: Optional[str]
    created_at: datetime

# Database connection and session management
def create_database_engine(database_url: str):
    """Create SQLAlchemy engine"""
    return create_engine(database_url, echo=False)

def create_tables(engine):
    """Create all tables"""
    Base.metadata.create_all(engine)

def get_db_session(engine):
    """Get database session"""
    Session = sessionmaker(bind=engine)
    return Session()

# Utility functions
def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return str(uuid.uuid4())

def generate_message_id() -> str:
    """Generate a unique message ID"""
    import uuid
    return str(uuid.uuid4())