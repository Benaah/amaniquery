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
            
            # For Neon databases, use unpooled connection to avoid parameter restrictions
            if "neon.tech" in database_url and "pooler" in database_url:
                unpooled_url = os.getenv("DATABASE_URL_UNPOOLED")
                if unpooled_url:
                    database_url = unpooled_url
                    logger.info("Using unpooled Neon connection for chat database")

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
    
    def get_session_with_user(self, session_id: str) -> Optional[ChatSession]:
        """Get chat session with user_id for ownership verification"""
        with get_db_session(self.engine) as db:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            return session

    def update_session_title(self, session_id: str, title: str):
        """Update session title"""
        with get_db_session(self.engine) as db:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.title = title
                db.commit()
                logger.info(f"Updated session {session_id} title to: {title}")

    def generate_session_title(self, session_id: str) -> str:
        """Generate a title for the session based on the first user message"""
        with get_db_session(self.engine) as db:
            # Get the first user message
            first_message = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.role == "user"
            ).order_by(ChatMessage.created_at).first()
            
            if first_message:
                content = first_message.content.strip()
                # Create a title from the first 50 characters, ending at word boundary
                if len(content) <= 50:
                    title = content
                else:
                    title = content[:50].rsplit(' ', 1)[0] + "..."
                
                # Update the session title
                self.update_session_title(session_id, title)
                return title
            
            return "New Chat"

    def list_sessions(self, user_id: Optional[str] = None, limit: int = 50) -> List[ChatSessionResponse]:
        """List chat sessions"""
        try:
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
        except Exception as e:
            logger.error(f"Database error in list_sessions: {e}")
            return []  # Return empty list on error

    def add_message(self, session_id: str, content: str, role: str,
                   token_count: Optional[int] = None, model_used: Optional[str] = None,
                   sources: Optional[List[Dict]] = None, attachments: Optional[List[Dict]] = None) -> str:
        """Add a message to a chat session"""
        message_id = generate_message_id()
        db = get_db_session(self.engine)
        
        try:
            message = ChatMessage(
                id=message_id,
                session_id=session_id,
                role=role,
                content=content,
                token_count=token_count,
                model_used=model_used,
                sources=sources,
                attachments=attachments
            )
            db.add(message)

            # Update session updated_at
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.updated_at = datetime.utcnow()

            db.commit()
            logger.info(f"Added {role} message {message_id} to session {session_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding message to session {session_id}: {e}")
            raise
        finally:
            db.close()

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
                attachments=msg.attachments,
                feedback_type=msg.feedback_type
            ) for msg in messages]
    
    def get_messages_by_message_id(self, message_id: str) -> List[ChatMessageResponse]:
        """Get a message by its ID (returns list for consistency)"""
        with get_db_session(self.engine) as db:
            message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
            if not message:
                return []
            
            return [ChatMessageResponse(
                id=message.id,
                session_id=message.session_id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
                token_count=message.token_count,
                model_used=message.model_used,
                sources=message.sources,
                attachments=message.attachments,
                feedback_type=message.feedback_type
            )]

    def add_feedback(self, message_id: str, feedback_type: str, comment: Optional[str] = None,
                    user_id: Optional[str] = None) -> int:
        """Add feedback for a message"""
        try:
            db = get_db_session(self.engine)
            try:
                # Validate that the message exists
                # Use explicit query with case-insensitive matching and trim whitespace
                message_id_clean = message_id.strip()
                
                # Refresh the session to ensure we see latest committed data
                db.expire_all()
                
                # Query for the message
                message = db.query(ChatMessage).filter(ChatMessage.id == message_id_clean).first()
                
                # If still not found, try refreshing and querying again
                if not message:
                    db.commit()  # Ensure any pending transactions are committed
                    db.expire_all()  # Clear any cached data
                    message = db.query(ChatMessage).filter(ChatMessage.id == message_id_clean).first()
                
                if not message:
                    # Enhanced debugging: Check if message exists with different approaches
                    logger.warning(f"Message {message_id_clean} not found with direct query. Attempting diagnostic queries...")
                    
                    # Try case-insensitive search
                    from sqlalchemy import func
                    message = db.query(ChatMessage).filter(
                        func.lower(ChatMessage.id) == func.lower(message_id_clean)
                    ).first()
                    
                    if message:
                        logger.warning(f"Found message with different case: {message.id} (requested: {message_id_clean})")
                        message_id_clean = message.id
                    else:
                        # Try to find any message with similar ID (for debugging)
                        similar_messages = db.query(ChatMessage.id, ChatMessage.session_id).filter(
                            ChatMessage.id.like(f"%{message_id_clean[-8:]}%")  # Last 8 chars
                        ).limit(5).all()
                        
                        # Get total message count
                        total_count = db.query(func.count(ChatMessage.id)).scalar()
                        
                        # Get sample message IDs
                        sample_messages = db.query(ChatMessage.id).order_by(ChatMessage.created_at.desc()).limit(5).all()
                        
                        error_details = {
                            "requested_id": message_id_clean,
                            "total_messages_in_db": total_count,
                            "sample_message_ids": [m.id for m in sample_messages],
                            "similar_ids_found": [m.id for m in similar_messages] if similar_messages else []
                        }
                        
                        logger.error(f"Message not found. Details: {error_details}")
                        error_msg = f"Message {message_id_clean} not found in database. Total messages: {total_count}"
                        raise ValueError(error_msg)
                
                # Check if feedback already exists for this message
                existing_feedback = db.query(UserFeedback).filter(
                    UserFeedback.message_id == message_id_clean,
                    UserFeedback.feedback_type == feedback_type
                ).first()
                
                if existing_feedback:
                    # Update existing feedback
                    if comment is not None:
                        existing_feedback.content = comment
                    existing_feedback.feedback_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"Updated {feedback_type} feedback for message {message_id_clean}")
                    return existing_feedback.id
                
                # Add new feedback
                feedback = UserFeedback(
                    user_id=user_id,
                    message_id=message_id_clean,
                    feedback_type=feedback_type,
                    content=comment
                )
                db.add(feedback)
                db.commit()
                
                logger.info(f"Added {feedback_type} feedback for message {message_id_clean}")
                return feedback.id
            finally:
                db.close()
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Database error in add_feedback: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def get_feedback_stats(self) -> Dict[str, int]:
        """Get feedback statistics"""
        with get_db_session(self.engine) as db:
            from sqlalchemy import func
            feedback_counts = db.query(
                UserFeedback.feedback_type,
                func.count(UserFeedback.id)
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

    def get_db_session(self):
        """Get database session for external use"""
        return get_db_session(self.engine)