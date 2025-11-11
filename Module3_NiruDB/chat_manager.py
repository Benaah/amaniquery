"""
Chat Database Manager
Handles chat sessions, messages, and feedback storage
"""
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from Module3_NiruDB.chat_models import (
    ChatSession, ChatMessage, UserFeedback,
    ChatSessionResponse, ChatMessageResponse, FeedbackResponse,
    create_database_engine, get_db_session, generate_session_id, generate_message_id
)


class ChatDatabaseManager:
    """Manage chat-related database operations"""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize chat database manager

        Args:
            database_url: PostgreSQL connection URL
        """
        if database_url is None:
            database_url = os.getenv("DATABASE_URL", "postgresql://localhost/amaniquery")

        self.database_url = database_url
        self.engine = create_database_engine(database_url)

        # Create tables if they don't exist
        from Module3_NiruDB.chat_models import create_tables
        create_tables(self.engine)

        logger.info("Chat database manager initialized")

    def create_session(self, title: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """Create a new chat session"""
        session_id = generate_session_id()

        with get_db_session(self.engine) as db:
            chat_session = ChatSession(
                id=session_id,
                title=title,
                user_id=user_id
            )
            db.add(chat_session)
            db.commit()

        logger.info(f"Created chat session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[ChatSessionResponse]:
        """Get chat session by ID"""
        with get_db_session(self.engine) as db:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                return None

            message_count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()

            return ChatSessionResponse(
                id=session.id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                is_active=session.is_active,
                message_count=message_count
            )

    def update_session_title(self, session_id: str, title: str):
        """Update session title"""
        with get_db_session(self.engine) as db:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.title = title
                db.commit()
                logger.info(f"Updated session {session_id} title to: {title}")

    def list_sessions(self, user_id: Optional[str] = None, limit: int = 50) -> List[ChatSessionResponse]:
        """List chat sessions"""
        with get_db_session(self.engine) as db:
            query = db.query(ChatSession)
            if user_id:
                query = query.filter(ChatSession.user_id == user_id)

            sessions = query.order_by(ChatSession.updated_at.desc()).limit(limit).all()

            result = []
            for session in sessions:
                message_count = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).count()
                result.append(ChatSessionResponse(
                    id=session.id,
                    title=session.title,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    is_active=session.is_active,
                    message_count=message_count
                ))

            return result

    def add_message(self, session_id: str, content: str, role: str,
                   token_count: Optional[int] = None, model_used: Optional[str] = None,
                   sources: Optional[List[Dict]] = None) -> str:
        """Add a message to a chat session"""
        message_id = generate_message_id()

        with get_db_session(self.engine) as db:
            message = ChatMessage(
                id=message_id,
                session_id=session_id,
                role=role,
                content=content,
                token_count=token_count,
                model_used=model_used,
                sources=sources
            )
            db.add(message)

            # Update session updated_at
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.updated_at = datetime.utcnow()

            db.commit()

        logger.info(f"Added {role} message to session {session_id}")
        return message_id

    def get_messages(self, session_id: str, limit: int = 100) -> List[ChatMessageResponse]:
        """Get messages for a session"""
        with get_db_session(self.engine) as db:
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at).limit(limit).all()

            return [ChatMessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                token_count=msg.token_count,
                model_used=msg.model_used,
                sources=msg.sources,
                feedback_type=msg.feedback_type
            ) for msg in messages]

    def add_feedback(self, message_id: str, feedback_type: str, comment: Optional[str] = None,
                    user_id: Optional[str] = None) -> int:
        """Add feedback for a message"""
        with get_db_session(self.engine) as db:
            # Update message feedback
            message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
            if message:
                message.feedback_type = feedback_type
                message.feedback_comment = comment
                message.feedback_at = datetime.utcnow()

            # Add to feedback table
            feedback = UserFeedback(
                user_id=user_id,
                message_id=message_id,
                feedback_type=feedback_type,
                content=comment
            )
            db.add(feedback)
            db.commit()

            logger.info(f"Added {feedback_type} feedback for message {message_id}")
            return feedback.id

    def get_feedback_stats(self) -> Dict[str, int]:
        """Get feedback statistics"""
        with get_db_session(self.engine) as db:
            feedback_counts = db.query(
                UserFeedback.feedback_type,
                db.func.count(UserFeedback.id)
            ).group_by(UserFeedback.feedback_type).all()

            return {feedback_type: count for feedback_type, count in feedback_counts}

    def delete_session(self, session_id: str):
        """Delete a chat session and all its messages"""
        with get_db_session(self.engine) as db:
            # This will cascade delete messages due to relationship
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                db.delete(session)
                db.commit()
                logger.info(f"Deleted chat session: {session_id}")

    def generate_session_title(self, session_id: str) -> str:
        """Generate a title for the session based on the first user message"""
        with get_db_session(self.engine) as db:
            first_message = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.role == "user"
            ).order_by(ChatMessage.created_at).first()

            if first_message:
                # Take first 50 characters and clean it up
                title = first_message.content[:50].strip()
                if len(first_message.content) > 50:
                    title += "..."
                return title

        return f"Chat Session {session_id[:8]}"