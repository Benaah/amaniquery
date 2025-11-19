"""
Rate Limiting Middleware
Implements token bucket algorithm for rate limiting
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Callable
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import status

from ..models.auth_models import RateLimit
from ..config import config
from Module3_NiruDB.chat_models import create_database_engine, get_db_session


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm"""
    
    def __init__(self, app, database_url: str = None):
        super().__init__(app)
        self.database_url = database_url or config.DATABASE_URL
        if self.database_url:
            self.engine = create_database_engine(self.database_url)
        else:
            self.engine = None
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with rate limiting"""
        # Skip rate limiting for public endpoints
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        if not self.engine:
            return await call_next(request)
        
        db = get_db_session(self.engine)
        
        try:
            # Get auth context
            auth_context = getattr(request.state, "auth_context", None)
            
            if not auth_context:
                # No auth - allow but with very restrictive limits
                return await call_next(request)
            
            # Get rate limit configuration
            rate_limit = self.get_or_create_rate_limit(db, auth_context, request.url.path)
            
            # Check rate limits
            if not self.check_rate_limit(db, rate_limit):
                db.close()
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": "Too many requests. Please try again later."
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_limit.limit_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": "60"
                    }
                )
            
            # Update rate limit counters
            self.update_rate_limit_counters(db, rate_limit)
            
            # Continue with request
            response = await call_next(request)
            
            # Add rate limit headers
            remaining_minute = max(0, rate_limit.limit_per_minute - rate_limit.current_minute_count)
            response.headers["X-RateLimit-Limit"] = str(rate_limit.limit_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(remaining_minute)
            
            return response
            
        finally:
            db.close()
    
    def get_or_create_rate_limit(
        self,
        db: Session,
        auth_context,
        endpoint: str
    ) -> RateLimit:
        """Get or create rate limit record"""
        # Determine limits based on tier (simplified - use defaults for now)
        limits = config.get_rate_limit("basic", endpoint)
        
        # Try to find existing rate limit
        if auth_context.user_id:
            rate_limit = db.query(RateLimit).filter(
                RateLimit.user_id == auth_context.user_id,
                RateLimit.endpoint == endpoint
            ).first()
        elif auth_context.integration_id:
            rate_limit = db.query(RateLimit).filter(
                RateLimit.integration_id == auth_context.integration_id,
                RateLimit.endpoint == endpoint
            ).first()
        elif auth_context.api_key_id:
            rate_limit = db.query(RateLimit).filter(
                RateLimit.api_key_id == auth_context.api_key_id,
                RateLimit.endpoint == endpoint
            ).first()
        else:
            # Create default rate limit
            rate_limit = RateLimit(
                endpoint=endpoint,
                limit_per_minute=limits["per_minute"],
                limit_per_hour=limits["per_hour"],
                limit_per_day=limits["per_day"],
            )
            db.add(rate_limit)
            db.commit()
            db.refresh(rate_limit)
            return rate_limit
        
        if not rate_limit:
            # Create new rate limit
            rate_limit = RateLimit(
                user_id=auth_context.user_id,
                integration_id=auth_context.integration_id,
                api_key_id=auth_context.api_key_id,
                endpoint=endpoint,
                limit_per_minute=limits["per_minute"],
                limit_per_hour=limits["per_hour"],
                limit_per_day=limits["per_day"],
            )
            db.add(rate_limit)
            db.commit()
            db.refresh(rate_limit)
        
        return rate_limit
    
    def check_rate_limit(self, db: Session, rate_limit: RateLimit) -> bool:
        """Check if rate limit allows request"""
        now = datetime.utcnow()
        
        # Reset counters if needed
        if not rate_limit.last_reset_minute or (now - rate_limit.last_reset_minute).total_seconds() >= 60:
            rate_limit.current_minute_count = 0
            rate_limit.last_reset_minute = now
        
        if not rate_limit.last_reset_hour or (now - rate_limit.last_reset_hour).total_seconds() >= 3600:
            rate_limit.current_hour_count = 0
            rate_limit.last_reset_hour = now
        
        if not rate_limit.last_reset_day or (now - rate_limit.last_reset_day).total_seconds() >= 86400:
            rate_limit.current_day_count = 0
            rate_limit.last_reset_day = now
        
        db.commit()
        
        # Check limits
        if rate_limit.current_minute_count >= rate_limit.limit_per_minute:
            return False
        if rate_limit.current_hour_count >= rate_limit.limit_per_hour:
            return False
        if rate_limit.current_day_count >= rate_limit.limit_per_day:
            return False
        
        return True
    
    def update_rate_limit_counters(self, db: Session, rate_limit: RateLimit):
        """Update rate limit counters after request"""
        rate_limit.current_minute_count += 1
        rate_limit.current_hour_count += 1
        rate_limit.current_day_count += 1
        rate_limit.updated_at = datetime.utcnow()
        db.commit()

