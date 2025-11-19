"""
Authentication and Authorization Routers
"""
from .user_router import router as user_router
from .admin_router import router as admin_router
from .integration_router import router as integration_router
from .api_key_router import router as api_key_router
from .oauth_router import router as oauth_router
from .analytics_router import router as analytics_router

__all__ = [
    "user_router",
    "admin_router",
    "integration_router",
    "api_key_router",
    "oauth_router",
    "analytics_router",
]

