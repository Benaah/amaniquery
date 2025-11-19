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
        # Generate tokens
        session_token = SessionProvider.generate_session_token()
        refresh_token = SessionProvider.generate_session_token()
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(hours=config.SESSION_EXPIRE_HOURS)
        
        # Create session
        session = UserSession(
            user_id=user.id,
            session_token=SessionProvider.hash_token(session_token),
            refresh_token=SessionProvider.hash_token(refresh_token),
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session_token, session
    
    @staticmethod
    def validate_session(db: Session, session_token: str) -> Optional[UserSession]:
        """Validate session token and return session"""
        token_hash = SessionProvider.hash_token(session_token)
        
        session = db.query(UserSession).filter(
            and_(
                UserSession.session_token == token_hash,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).first()
        
        if session:
            # Update last activity
            session.last_activity = datetime.utcnow()
            db.commit()
        
        return session
    
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

