"""
Authentication Middleware
Validates credentials and attaches authentication context to requests
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from typing import Optional, Callable
from sqlalchemy.orm import Session
from fastapi import status, HTTPException

from ..models.auth_models import User, Integration
from ..models.pydantic_models import AuthContext
from ..providers.api_key_provider import APIKeyProvider
from ..providers.oauth2_provider import OAuth2Provider
from ..providers.jwt_provider import JWTProvider
from ..providers.session_provider import SessionProvider
from ..config import config
from Module3_NiruDB.chat_models import create_database_engine, get_db_session


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for FastAPI"""
    
    # Public endpoints that don't require authentication
    PUBLIC_ENDPOINTS = [
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/password/reset-request",
        "/api/v1/auth/password/reset",
        "/api/v1/auth/email/verify",
        "/api/v1/auth/email/verify-request",
    ]
    
    def __init__(self, app, database_url: Optional[str] = None):
        super().__init__(app)
        self.database_url = database_url or config.DATABASE_URL
        if self.database_url:
            self.engine = create_database_engine(self.database_url)
        else:
            self.engine = None
    
    def is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public"""
        # Check exact match
        if path in self.PUBLIC_ENDPOINTS:
            return True
        
        # Check prefix match (for /api/v1/auth/* endpoints)
        for public_path in self.PUBLIC_ENDPOINTS:
            if path.startswith(public_path):
                return True
        
        # Admin routes are explicitly NOT public, they are handled by AdminAuthMiddleware
        if path.startswith("/admin"):
            return False
        
        return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and attach auth context"""
        # Skip authentication for public endpoints
        if self.is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Skip if no database connection
        if not self.engine:
            return await call_next(request)
        
        # Get database session
        db = get_db_session(self.engine)
        auth_context = None
        
        try:
            # Try to authenticate
            auth_context = await self.authenticate_request(request, db)
            
            # Attach auth context to request state (even if None, for optional auth endpoints)
            request.state.auth_context = auth_context
            
            # Continue with request
            response = await call_next(request)
            
            return response
            
        except HTTPException as e:
            db.close()
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            db.close()
            import traceback
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Authentication error", "detail": str(e), "traceback": traceback.format_exc()}
            )
        finally:
            db.close()
    
    async def authenticate_request(self, request: Request, db: Session) -> Optional[AuthContext]:
        """Authenticate request and return auth context"""
        # Try different authentication methods in order
        
        # 1. Try API Key (X-API-Key header)
        api_key = request.headers.get("X-API-Key")
        if api_key:
            api_key_record = APIKeyProvider.validate_api_key(db, api_key)
            if api_key_record:
                user = None
                integration = None
                
                if api_key_record.user_id:
                    user = db.query(User).filter(User.id == api_key_record.user_id).first()
                elif api_key_record.integration_id:
                    integration = db.query(Integration).filter(Integration.id == api_key_record.integration_id).first()
                
                if user or integration:
                    return AuthContext(
                        auth_method="api_key",
                        user_id=user.id if user else None,
                        integration_id=integration.id if integration else None,
                        api_key_id=api_key_record.id,
                        scopes=api_key_record.scopes or []
                    )
        
        # 2. Try Bearer token (JWT or OAuth)
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]  # Remove "Bearer " prefix
            
            # Try OAuth token first
            oauth_token = OAuth2Provider.validate_access_token(db, token)
            if oauth_token:
                user = None
                if oauth_token.user_id:
                    user = db.query(User).filter(User.id == oauth_token.user_id).first()
                
                return AuthContext(
                    auth_method="oauth2",
                    user_id=user.id if user else None,
                    integration_id=None,
                    scopes=oauth_token.scopes or []
                )
            
            # Try JWT token
            jwt_payload = JWTProvider.validate_token(token)
            if jwt_payload:
                user = None
                integration = None
                
                if jwt_payload.get("user_id"):
                    user = db.query(User).filter(User.id == jwt_payload["user_id"]).first()
                if jwt_payload.get("integration_id"):
                    integration = db.query(Integration).filter(Integration.id == jwt_payload["integration_id"]).first()
                
                if user or integration:
                    return AuthContext(
                        auth_method="jwt",
                        user_id=user.id if user else None,
                        integration_id=integration.id if integration else None,
                        scopes=jwt_payload.get("scopes", [])
                    )
        
        # 3. Try session token (Cookie or X-Session-Token header)
        session_token = request.cookies.get("session_token") or request.headers.get("X-Session-Token")
        if session_token:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Attempting session authentication for {request.url.path}, token_length={len(session_token)}")
            
            session = SessionProvider.validate_session(db, session_token)
            if session:
                user = db.query(User).filter(User.id == session.user_id).first()
                if user:
                    logger.debug(f"Session authentication successful for user {user.id}")
                    return AuthContext(
                        auth_method="session",
                        user_id=user.id,
                        integration_id=None
                    )
                else:
                    # Log warning if session exists but user doesn't
                    logger.warning(f"Session found but user not found: session.user_id={session.user_id}")
            else:
                # Log detailed warning if session token provided but not valid
                from ..models.auth_models import UserSession
                from sqlalchemy import and_
                from datetime import datetime
                token_hash = SessionProvider.hash_token(session_token)
                existing_session = db.query(UserSession).filter(
                    UserSession.session_token == token_hash
                ).first()
                if existing_session:
                    logger.warning(
                        f"Session validation failed for {request.url.path}: "
                        f"is_active={existing_session.is_active}, "
                        f"expires_at={existing_session.expires_at}, "
                        f"now={datetime.utcnow()}, "
                        f"expired={existing_session.expires_at < datetime.utcnow() if existing_session.expires_at else 'N/A'}"
                    )
                else:
                    logger.warning(f"No session found in database for token (path: {request.url.path}, token_length: {len(session_token)})")
        
        # No authentication found - return None (endpoint may be optional auth)
        return None

