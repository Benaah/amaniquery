"""
Session Provider
Handles user session management
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.auth_models import UserSession, User
from ..config import config


class SessionProvider:
    """Handles user session operations"""
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash session token for storage"""
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(config.SESSION_TOKEN_LENGTH)
    
    @staticmethod
    def create_session(
        db: Session,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[str, UserSession]:
        """Create a new user session"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Generate tokens
            session_token = SessionProvider.generate_session_token()
            refresh_token = SessionProvider.generate_session_token()
            token_hash = SessionProvider.hash_token(session_token)
            
            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(hours=config.SESSION_EXPIRE_HOURS)
            
            logger.info(f"Creating session for user {user.id}, expires_at={expires_at}")
            
            # Create session
            session = UserSession(
                user_id=user.id,
                session_token=token_hash,
                refresh_token=SessionProvider.hash_token(refresh_token),
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            # Add session to database
            db.add(session)
            
            # Flush to get the session ID before commit
            db.flush()
            
            # Commit the transaction
            db.commit()
            
            # Refresh to ensure we have the latest data from database
            db.refresh(session)
            
            # Verify session was saved by querying it back
            saved_session = db.query(UserSession).filter(
                UserSession.session_token == token_hash
            ).first()
            
            if not saved_session:
                logger.error(f"Session was not saved to database! user_id={user.id}, token_hash={token_hash[:16]}...")
                db.rollback()
                raise Exception("Failed to save session to database")
            
            logger.info(f"Session created successfully: session_id={session.id}, user_id={user.id}, expires_at={session.expires_at}")
            
            return session_token, session
            
        except Exception as e:
            logger.error(f"Error creating session for user {user.id}: {e}", exc_info=True)
            db.rollback()
            raise
    
    @staticmethod
    def validate_session(db: Session, session_token: str) -> Optional[UserSession]:
        """Validate session token and return session"""
        from datetime import datetime
        from sqlalchemy import and_
        import logging
        
        logger = logging.getLogger(__name__)
        token_hash = SessionProvider.hash_token(session_token)
        now = datetime.utcnow()
        
        logger.info(f"Validating session: token_length={len(session_token)}, token_hash={token_hash[:16]}...")
        
        try:
            # Refresh database session to ensure we see latest data
            db.expire_all()
            
            # First check if session exists with matching token hash
            session = db.query(UserSession).filter(
                UserSession.session_token == token_hash
            ).first()
            
            if not session:
                logger.warning(f"Session not found for token hash: {token_hash[:16]}...")
                # Try one more time with explicit refresh
                try:
                    db.commit()  # Commit any pending transactions
                except:
                    pass
                db.expire_all()
                session = db.query(UserSession).filter(
                    UserSession.session_token == token_hash
                ).first()
                if not session:
                    logger.warning(f"Session still not found after refresh")
                    return None
            
            logger.info(f"Session found: id={session.id}, is_active={session.is_active}, expires_at={session.expires_at}, now={now}, user_id={session.user_id}")
            
            # Check if session is active
            if not session.is_active:
                logger.warning(f"Session found but not active: session_id={session.id}, is_active={session.is_active}")
                return None
            
            logger.debug(f"Session is active, checking expiration...")
            
            # Check if session is expired
            if session.expires_at:
                # Ensure both datetimes are timezone-naive for comparison
                expires_at = session.expires_at
                if hasattr(expires_at, 'replace') and expires_at.tzinfo is not None:
                    # Convert timezone-aware to naive UTC
                    expires_at = expires_at.replace(tzinfo=None)
                
                is_expired = expires_at <= now
                time_diff = (expires_at - now).total_seconds()
                logger.info(f"Session expiration check: expires_at={expires_at}, now={now}, expired={is_expired}, time_diff={time_diff} seconds")
                if is_expired:
                    logger.warning(f"Session expired: expires_at={expires_at}, now={now}, time_diff={time_diff} seconds")
                    return None
            else:
                logger.warning(f"Session has no expires_at: session_id={session.id}")
                return None
            
            logger.debug(f"Session expiration check passed, updating last_activity...")
            
            # Session is valid - update last activity
            try:
                session.last_activity = now
                db.commit()
                logger.info(f"Session validated successfully: session_id={session.id}, user_id={session.user_id}")
            except Exception as e:
                logger.error(f"Error updating session last_activity: {e}", exc_info=True)
                db.rollback()
                # Still return the session even if update fails
                logger.info(f"Returning session despite last_activity update failure: session_id={session.id}")
            
            logger.info(f"Returning validated session: session_id={session.id}, user_id={session.user_id}")
            return session
        except Exception as e:
            logger.error(f"Error validating session: {e}", exc_info=True)
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            try:
                db.rollback()
            except:
                pass
            return None
    
    @staticmethod
    def refresh_session(db: Session, refresh_token: str) -> Optional[Tuple[str, UserSession]]:
        """Refresh session using refresh token"""
        token_hash = SessionProvider.hash_token(refresh_token)
        
        session = db.query(UserSession).filter(
            and_(
                UserSession.refresh_token == token_hash,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not session:
            return None
        
        # Check if refresh is needed (within threshold)
        refresh_threshold = datetime.utcnow() + timedelta(hours=config.SESSION_REFRESH_THRESHOLD_HOURS)
        
        if session.expires_at > refresh_threshold:
            # Still valid, just return existing
            return None, session
        
        # Generate new session token
        new_session_token = SessionProvider.generate_session_token()
        new_expires_at = datetime.utcnow() + timedelta(hours=config.SESSION_EXPIRE_HOURS)
        
        # Update session
        session.session_token = SessionProvider.hash_token(new_session_token)
        session.expires_at = new_expires_at
        session.last_activity = datetime.utcnow()
        
        db.commit()
        db.refresh(session)
        
        return new_session_token, session
    
    @staticmethod
    def revoke_session(db: Session, session_token: str) -> bool:
        """Revoke a session"""
        token_hash = SessionProvider.hash_token(session_token)
        
        session = db.query(UserSession).filter(
            UserSession.session_token == token_hash
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def revoke_all_user_sessions(db: Session, user_id: str) -> int:
        """Revoke all sessions for a user"""
        sessions = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).all()
        
        count = len(sessions)
        for session in sessions:
            session.is_active = False
        
        db.commit()
        return count
    
    @staticmethod
    def cleanup_expired_sessions(db: Session) -> int:
        """Clean up expired sessions"""
        expired = db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired)
        for session in expired:
            session.is_active = False
        
        db.commit()
        return count

