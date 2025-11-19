"""
User Authentication Router
Handles user registration, login, profile management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional

from ..models.pydantic_models import (
    UserRegister, UserLogin, UserResponse, UserProfileUpdate,
    PasswordChange, PasswordResetRequest, PasswordReset,
    EmailVerificationRequest, SessionResponse
)
from ..providers.user_auth_provider import UserAuthProvider
from ..providers.session_provider import SessionProvider
from ..dependencies import get_db, get_current_user
from ..models.auth_models import User

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user (phone verification required after registration)"""
    try:
        user = UserAuthProvider.create_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            name=user_data.name,
            phone_number=user_data.phone_number
        )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            status=user.status,
            email_verified=user.email_verified,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=SessionResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user and create session"""
    try:
        user = UserAuthProvider.authenticate_user(
            db=db,
            email=login_data.email,
            password=login_data.password,
            ip_address=request.client.host if request.client else None
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create session
        session_token, session = SessionProvider.create_session(
            db=db,
            user=user,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return SessionResponse(
            session_token=session_token,
            refresh_token=None,  # Session-based, no separate refresh token
            expires_at=session.expires_at,
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                status=user.status,
                email_verified=user.email_verified,
                last_login=user.last_login,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """Logout user and invalidate session"""
    session_token = request.cookies.get("session_token") or request.headers.get("X-Session-Token")
    
    if session_token:
        SessionProvider.revoke_session(db, session_token)
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        status=user.status,
        email_verified=user.email_verified,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if profile_data.name is not None:
        user.name = profile_data.name
    if profile_data.email is not None:
        # Check if email already exists
        existing = db.query(User).filter(User.email == profile_data.email.lower()).first()
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = profile_data.email.lower()
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        status=user.status,
        email_verified=user.email_verified,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/password/change")
async def change_password(
    password_data: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password"""
    success = UserAuthProvider.change_password(
        db=db,
        user=user,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password changed successfully"}


@router.post("/password/reset-request")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    token = UserAuthProvider.request_password_reset(db, reset_data.email)
    
    # In production, send email with reset token
    # For now, just return success (token would be sent via email)
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password/reset")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """Reset password with token"""
    success = UserAuthProvider.reset_password(
        db=db,
        token=reset_data.token,
        new_password=reset_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"message": "Password reset successfully"}


@router.post("/email/verify-request")
async def request_email_verification(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request email verification"""
    token = UserAuthProvider.request_email_verification(db, user)
    
    # In production, send email with verification token
    return {"message": "Verification email sent"}


@router.get("/email/verify")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify email with token"""
    success = UserAuthProvider.verify_email(db, token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    return {"message": "Email verified successfully"}

