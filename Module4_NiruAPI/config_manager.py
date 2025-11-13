"""
Configuration Manager for Encrypted API Keys and Settings
"""
import os
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger

Base = declarative_base()

class ConfigEntry(Base):
    """Database model for configuration entries"""
    __tablename__ = "configurations"

    key = Column(String(255), primary_key=True)
    encrypted_value = Column(Text, nullable=False)
    description = Column(String(500))

class ConfigManager:
    """Manage encrypted configuration storage"""

    def __init__(self, database_url: Optional[str] = None, encryption_key: Optional[str] = None):
        """
        Initialize config manager

        Args:
            database_url: PostgreSQL connection URL
            encryption_key: Base64 encoded encryption key
        """
        if database_url is None:
            database_url = os.getenv("DATABASE_URL", "postgresql://localhost/amaniquery")

        if encryption_key is None:
            encryption_key = os.getenv("CONFIG_ENCRYPTION_KEY")
            if not encryption_key:
                # Generate a new key if not provided
                encryption_key = Fernet.generate_key().decode()
                logger.warning(f"Generated new encryption key: {encryption_key}")
                logger.warning("Store this key securely in CONFIG_ENCRYPTION_KEY environment variable")

        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.cipher = Fernet(encryption_key.encode())

        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info("Config manager initialized")

    def _get_db(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def set_config(self, key: str, value: str, description: str = ""):
        """Set encrypted configuration value"""
        encrypted_value = self.cipher.encrypt(value.encode()).decode()

        with self._get_db() as db:
            # Check if exists
            entry = db.query(ConfigEntry).filter(ConfigEntry.key == key).first()
            if entry:
                entry.encrypted_value = encrypted_value
                entry.description = description
            else:
                entry = ConfigEntry(key=key, encrypted_value=encrypted_value, description=description)
                db.add(entry)
            db.commit()
        logger.info(f"Set config: {key}")

    def get_config(self, key: str) -> Optional[str]:
        """Get decrypted configuration value"""
        with self._get_db() as db:
            entry = db.query(ConfigEntry).filter(ConfigEntry.key == key).first()
            if entry:
                try:
                    return self.cipher.decrypt(entry.encrypted_value.encode()).decode()
                except Exception as e:
                    logger.error(f"Failed to decrypt config {key}: {e}")
                    return None
        return None

    def delete_config(self, key: str):
        """Delete configuration entry"""
        with self._get_db() as db:
            entry = db.query(ConfigEntry).filter(ConfigEntry.key == key).first()
            if entry:
                db.delete(entry)
                db.commit()
                logger.info(f"Deleted config: {key}")

    def list_configs(self) -> Dict[str, Dict[str, Any]]:
        """List all configuration keys with descriptions"""
        with self._get_db() as db:
            entries = db.query(ConfigEntry).all()
            return {
                entry.key: {
                    "description": entry.description,
                    "has_value": bool(entry.encrypted_value)
                }
                for entry in entries
            }