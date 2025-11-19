"""
User Authentication Provider
Handles user registration, login, password management
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
import bcrypt
from loguru import logger

from ..models.auth_models import User
from ..config import config


class UserAuthProvider:
    """Handles user authentication operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def create_user(db: Session, email: str, password: str, name: Optional[str] = None, phone_number: Optional[str] = None) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email.lower()).first()
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Normalize phone number if provided
        normalized_phone = None
        if phone_number:
            phone = phone_number.strip().replace(" ", "").replace("-", "")
            if phone.startswith("0"):
                normalized_phone = "+254" + phone[1:]
            elif not phone.startswith("+"):
                normalized_phone = "+254" + phone
            else:
                normalized_phone = phone
        
        # Hash password
        password_hash = UserAuthProvider.hash_password(password)
        
        # Generate email verification token
        verification_token = secrets.token_urlsafe(32)
        
        # Create user (status pending_verification until phone is verified)
        user = User(
            email=email.lower(),
            password_hash=password_hash,
            name=name,
            phone_number=normalized_phone,
            phone_verified=False,
            email_verification_token=verification_token,
            status="pending_verification",  # Require phone verification
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Created user: {user.email}")
        return user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str, ip_address: Optional[str] = None) -> Optional[User]:
        """Authenticate user with email and password"""
        user = db.query(User).filter(User.email == email.lower()).first()
        
        if not user:
            # Don't reveal if user exists
            return None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise ValueError("Account is temporarily locked due to too many failed login attempts")
        
        # Verify password
        if not UserAuthProvider.verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= config.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=config.LOCKOUT_DURATION_MINUTES)
                logger.warning(f"Account locked for {user.email} due to too many failed attempts")
            db.commit()
            return None
        
        # Successful login - reset failed attempts and update last login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        user.last_login_ip = ip_address
        db.commit()
        
        logger.info(f"User authenticated: {user.email}")
        return user
    
    @staticmethod
    def request_password_reset(db: Session, email: str) -> Optional[str]:
        """Request password reset - returns reset token"""
        user = db.query(User).filter(User.email == email.lower()).first()
        
        if not user:
            # Don't reveal if user exists
            return None
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=config.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        
        db.commit()
        
        logger.info(f"Password reset requested for: {user.email}")
        return reset_token
    
    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        """Reset password using token"""
        user = db.query(User).filter(
            and_(
                User.password_reset_token == token,
                User.password_reset_expires > datetime.utcnow()
            )
        ).first()
        
        if not user:
            return False
        
        # Update password
        user.password_hash = UserAuthProvider.hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.failed_login_attempts = 0
        user.locked_until = None
        
        db.commit()
        
        logger.info(f"Password reset for: {user.email}")
        return True
    
    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str) -> bool:
        """Change password for authenticated user"""
        if not UserAuthProvider.verify_password(current_password, user.password_hash):
            return False
        
        user.password_hash = UserAuthProvider.hash_password(new_password)
        db.commit()
        
        logger.info(f"Password changed for: {user.email}")
        return True
    
    @staticmethod
    def verify_email(db: Session, token: str) -> bool:
        """Verify email using token"""
        user = db.query(User).filter(User.email_verification_token == token).first()
        
        if not user:
            return False
        
        user.email_verified = True
        user.email_verification_token = None
        if user.status == "pending_verification":
            user.status = "active"
        
        db.commit()
        
        logger.info(f"Email verified for: {user.email}")
        return True
    
    @staticmethod
    def request_email_verification(db: Session, user: User) -> str:
        """Request new email verification token"""
        verification_token = secrets.token_urlsafe(32)
        user.email_verification_token = verification_token
        db.commit()
        
        return verification_token
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email.lower()).first()

