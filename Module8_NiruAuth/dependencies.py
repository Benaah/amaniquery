"""
FastAPI Dependencies for Authentication
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from .models.auth_models import User, Integration
from .models.pydantic_models import AuthContext
from .authorization.permission_checker import PermissionChecker
from .authorization.user_role_manager import UserRoleManager
from Module3_NiruDB.chat_models import create_database_engine, get_db_session
from .config import config


# Database dependency
def get_db():
    """Get database session"""
    if not config.DATABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured"
        )
    
    engine = create_database_engine(config.DATABASE_URL)
    db = get_db_session(engine)
    try:
        yield db
    finally:
        db.close()


def get_auth_context(request: Request) -> Optional[AuthContext]:
    """Get authentication context from request state"""
    return getattr(request.state, "auth_context", None)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    auth_context = get_auth_context(request)
    
    if not auth_context or not auth_context.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    user = db.query(User).filter(User.id == auth_context.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    return user


def get_current_integration(
    request: Request,
    db: Session = Depends(get_db)
) -> Integration:
    """Get current authenticated integration"""
    auth_context = get_auth_context(request)
    
    if not auth_context or not auth_context.integration_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Integration authentication required"
        )
    
    integration = db.query(Integration).filter(Integration.id == auth_context.integration_id).first()
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Integration not found"
        )
    
    if integration.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Integration is not active"
        )
    
    return integration


def get_current_auth(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current authenticated user or integration"""
    auth_context = get_auth_context(request)
    
    if not auth_context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    if auth_context.user_id:
        return get_current_user(request, db)
    elif auth_context.integration_id:
        return get_current_integration(request, db)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )


def require_auth(
    request: Request,
    db: Session = Depends(get_db)
) -> AuthContext:
    """Require authentication (user or integration)"""
    auth_context = get_auth_context(request)
    
    if not auth_context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return auth_context


def require_role(role_name: str):
    """Dependency factory for requiring a specific role"""
    def role_checker(
        request: Request,
        db: Session = Depends(get_db)
    ):
        auth_context = get_auth_context(request)
        
        if not auth_context or not auth_context.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user = db.query(User).filter(User.id == auth_context.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check if user has the required role
        from .authorization.role_manager import RoleManager
        user_roles = RoleManager.get_user_roles(db, user.id)
        role_names = [role.name for role in user_roles]
        
        if role_name not in role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required"
            )
        
        return user
    
    return role_checker


def require_permission(permission: str):
    """Dependency factory for requiring a specific permission"""
    def permission_checker(
        request: Request,
        db: Session = Depends(get_db)
    ):
        auth_context = get_auth_context(request)
        
        if not auth_context:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user = None
        integration = None
        
        if auth_context.user_id:
            user = db.query(User).filter(User.id == auth_context.user_id).first()
        elif auth_context.integration_id:
            integration = db.query(Integration).filter(Integration.id == auth_context.integration_id).first()
        
        if not user and not integration:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User or integration not found"
            )
        
        # Check permission
        if not PermissionChecker.has_permission(db, user, integration, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        
        return user or integration
    
    return permission_checker


def require_admin(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Require admin role"""
    user = get_current_user(request, db)
    
    if not UserRoleManager.is_admin(db, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user


# Optional auth - doesn't raise exception if not authenticated
def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None


def get_optional_integration(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[Integration]:
    """Get current integration if authenticated, None otherwise"""
    try:
        return get_current_integration(request, db)
    except HTTPException:
        return None

