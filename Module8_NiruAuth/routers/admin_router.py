"""
Admin Router
Admin endpoints for user management, role management, etc.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..models.pydantic_models import (
    UserResponse, UserListResponse, UserUpdate, RoleResponse,
    RoleCreate, RoleUpdate, UserRoleAssign
)
from ..dependencies import get_db, require_admin
from ..models.auth_models import User, Role
from ..authorization.role_manager import RoleManager
from ..authorization.user_role_manager import UserRoleManager

router = APIRouter(prefix="/api/v1/auth/admin", tags=["Admin"])


# User Management
@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    offset = (page - 1) * page_size
    users = db.query(User).offset(offset).limit(page_size).all()
    total = db.query(User).count()
    
    return UserListResponse(
        users=[
            UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                status=user.status,
                email_verified=user.email_verified,
                last_login=user.last_login,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
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


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.email is not None:
        existing = db.query(User).filter(User.email == user_data.email.lower()).first()
        if existing and existing.id != user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
        user.email = user_data.email.lower()
    if user_data.status is not None:
        user.status = user_data.status
    if user_data.email_verified is not None:
        user.email_verified = user_data.email_verified
    
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


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/roles", response_model=RoleResponse)
async def assign_role_to_user(
    user_id: str,
    role_data: UserRoleAssign,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Assign role to user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user_role = RoleManager.assign_role_to_user(db, user_id, role_data.role_id, admin.id)
    role = db.query(Role).filter(Role.id == role_data.role_id).first()
    
    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        role_type=role.role_type,
        permissions=role.permissions,
        is_system=role.is_system,
        created_at=role.created_at
    )


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Remove role from user (admin only)"""
    success = RoleManager.remove_role_from_user(db, user_id, role_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role assignment not found")
    
    return {"message": "Role removed successfully"}


# Role Management
@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    role_type: Optional[str] = Query(None),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all roles (admin only)"""
    roles = RoleManager.list_roles(db, role_type)
    return [
        RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            role_type=role.role_type,
            permissions=role.permissions,
            is_system=role.is_system,
            created_at=role.created_at
        )
        for role in roles
    ]


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new role (admin only)"""
    try:
        role = RoleManager.create_role(
            db=db,
            name=role_data.name,
            description=role_data.description,
            role_type=role_data.role_type,
            permissions=role_data.permissions or []
        )
        
        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            role_type=role.role_type,
            permissions=role.permissions,
            is_system=role.is_system,
            created_at=role.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

