#!/usr/bin/env python3
"""
Seed Admin User Script
Creates an admin user in the database with all required fields and admin role
"""
import os
import sys
from pathlib import Path
from getpass import getpass

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from loguru import logger

from Module3_NiruDB.chat_models import create_database_engine
from Module8_NiruAuth.models.auth_models import User, Role, UserRole
from Module8_NiruAuth.providers.user_auth_provider import UserAuthProvider
from Module8_NiruAuth.authorization.role_manager import RoleManager
from Module8_NiruAuth.models.enums import UserStatus

load_dotenv()


def seed_admin_user(
    email: str,
    password: str,
    name: str = None,
    phone_number: str = None,
    skip_verification: bool = True
):
    """
    Seed an admin user in the database
    
    Args:
        email: Admin user email (required)
        password: Admin user password (required)
        name: Admin user name (optional)
        phone_number: Admin user phone number (optional)
        skip_verification: Skip email/phone verification for admin (default: True)
    """
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        logger.error("Please set DATABASE_URL in your .env file")
        sys.exit(1)
    
    logger.info(f"Connecting to database...")
    
    try:
        # Create database engine
        engine = create_database_engine(database_url)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        try:
            # Check if admin user already exists
            existing_user = db.query(User).filter(User.email == email.lower()).first()
            if existing_user:
                logger.warning(f"User with email '{email}' already exists!")
                response = input("Do you want to update this user to admin? (y/n): ").strip().lower()
                if response != 'y':
                    logger.info("Aborted.")
                    return
                
                # Update existing user
                user = existing_user
                logger.info(f"Updating existing user: {user.email}")
            else:
                # Create new user
                logger.info(f"Creating new admin user: {email}")
                user = User(
                    email=email.lower(),
                    password_hash=UserAuthProvider.hash_password(password),
                    name=name,
                    phone_number=phone_number,
                    phone_verified=skip_verification,
                    email_verified=skip_verification,
                    status=UserStatus.ACTIVE.value,
                    email_verification_token=None,
                    failed_login_attempts=0,
                    locked_until=None,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"✅ User created: {user.id}")
            
            # Ensure default roles exist
            logger.info("Ensuring default roles exist...")
            RoleManager.get_or_create_default_roles(db)
            
            # Get or create admin role
            admin_role = RoleManager.get_role_by_name(db, "admin")
            if not admin_role:
                logger.error("Admin role not found! This should not happen if migrations ran correctly.")
                logger.info("Creating admin role manually...")
                admin_role = Role(
                    name="admin",
                    description="Administrator with full access",
                    role_type="user",
                    permissions=["*"],  # All permissions
                    is_system=True
                )
                db.add(admin_role)
                db.commit()
                db.refresh(admin_role)
                logger.info("✅ Admin role created")
            else:
                logger.info(f"✅ Admin role found: {admin_role.id}")
            
            # Assign admin role to user
            logger.info("Assigning admin role to user...")
            user_role = RoleManager.assign_role_to_user(
                db=db,
                user_id=user.id,
                role_id=admin_role.id,
                assigned_by=user.id  # Self-assigned for initial admin
            )
            logger.info(f"✅ Admin role assigned to user")
            
            # Update user if needed (for existing users)
            if existing_user:
                # Update password if provided
                if password:
                    user.password_hash = UserAuthProvider.hash_password(password)
                    logger.info("✅ Password updated")
                
                # Update status and verification
                user.status = UserStatus.ACTIVE.value
                user.email_verified = skip_verification
                user.phone_verified = skip_verification
                user.email_verification_token = None
                user.failed_login_attempts = 0
                user.locked_until = None
                
                # Update optional fields
                if name:
                    user.name = name
                if phone_number:
                    user.phone_number = phone_number
                
                db.commit()
                logger.info("✅ User updated")
            
            # Verify the setup
            logger.info("\n" + "="*60)
            logger.info("✅ Admin user seeded successfully!")
            logger.info("="*60)
            logger.info(f"User ID: {user.id}")
            logger.info(f"Email: {user.email}")
            logger.info(f"Name: {user.name or 'Not set'}")
            logger.info(f"Status: {user.status}")
            logger.info(f"Email Verified: {user.email_verified}")
            logger.info(f"Phone Verified: {user.phone_verified}")
            
            # Check roles
            user_roles = RoleManager.get_user_roles(db, user.id)
            logger.info(f"Roles: {[role.name for role in user_roles]}")
            logger.info("="*60)
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error seeding admin user: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


def main():
    """Interactive admin user seeding"""
    logger.info("🚀 AmaniQuery Admin User Seeding")
    logger.info("="*60)
    
    # Get email
    email = input("Enter admin email: ").strip()
    if not email:
        logger.error("Email is required!")
        sys.exit(1)
    
    # Validate email format (basic check)
    if "@" not in email or "." not in email.split("@")[1]:
        logger.warning("Email format looks invalid, but continuing...")
    
    # Get password
    password = getpass("Enter admin password: ").strip()
    if not password:
        logger.error("Password is required!")
        sys.exit(1)
    
    if len(password) < 8:
        logger.warning("Password is less than 8 characters. Consider using a stronger password.")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            logger.info("Aborted.")
            sys.exit(0)
    
    # Confirm password
    password_confirm = getpass("Confirm admin password: ").strip()
    if password != password_confirm:
        logger.error("Passwords do not match!")
        sys.exit(1)
    
    # Get optional fields
    name = input("Enter admin name (optional, press Enter to skip): ").strip() or None
    phone_number = input("Enter phone number (optional, press Enter to skip): ").strip() or None
    
    # Normalize phone number if provided
    if phone_number:
        phone = phone_number.strip().replace(" ", "").replace("-", "")
        if phone.startswith("0"):
            phone_number = "+254" + phone[1:]
        elif not phone.startswith("+"):
            phone_number = "+254" + phone
        else:
            phone_number = phone
    
    logger.info("\n" + "="*60)
    logger.info("Summary:")
    logger.info(f"  Email: {email}")
    logger.info(f"  Name: {name or 'Not set'}")
    logger.info(f"  Phone: {phone_number or 'Not set'}")
    logger.info("="*60)
    
    confirm = input("\nProceed with creating admin user? (y/n): ").strip().lower()
    if confirm != 'y':
        logger.info("Aborted.")
        sys.exit(0)
    
    # Seed the admin user
    seed_admin_user(
        email=email,
        password=password,
        name=name,
        phone_number=phone_number,
        skip_verification=True
    )
    
    logger.info("\n🎉 Admin user seeding completed!")
    logger.info("\nYou can now log in with this admin account.")


if __name__ == "__main__":
    main()

