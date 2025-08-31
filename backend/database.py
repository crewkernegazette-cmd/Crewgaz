from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
import os

# Database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost/crewkerne_gazette')

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Enums
class ArticleCategory(str, Enum):
    NEWS = "news"
    MUSIC = "music"
    DOCUMENTARIES = "documentaries" 
    COMEDY = "comedy"

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

# SQLAlchemy Models
class DBUser(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class DBArticle(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, nullable=False)  # Keep UUID for URLs
    title = Column(String(255), nullable=False)
    subheading = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    category = Column(SQLEnum(ArticleCategory), nullable=False)
    publisher_name = Column(String(100), default="The Crewkerne Gazette")
    author_name = Column(String(100), nullable=True)
    author_id = Column(String(50), nullable=True)
    featured_image = Column(String(500), nullable=True)  # URL to image
    image_caption = Column(String(255), nullable=True)
    video_url = Column(String(500), nullable=True)
    tags = Column(Text, nullable=True)  # JSON string of tags
    is_breaking = Column(Boolean, default=False, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class DBContact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DBSettings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_database():
    """Create tables and initial data"""
    Base.metadata.create_all(bind=engine)
    
    # Create initial admin user and settings
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = db.query(DBUser).filter(DBUser.username == "admin").first()
        if not admin_user:
            from server import hash_password
            admin_user = DBUser(
                username="admin",
                email="admin@crewkernegazette.co.uk",
                password_hash=hash_password("admin123"),
                role=UserRole.ADMIN
            )
            db.add(admin_user)
        
        # Check if admin_backup user exists
        backup_user = db.query(DBUser).filter(DBUser.username == "admin_backup").first()
        if not backup_user:
            from server import hash_password
            backup_user = DBUser(
                username="admin_backup", 
                email="backup@crewkernegazette.co.uk",
                password_hash=hash_password("admin_backup"),
                role=UserRole.ADMIN
            )
            db.add(backup_user)
            
        # Create default settings
        settings_defaults = [
            ("maintenance_mode", "false"),
            ("show_breaking_news_banner", "true"),
            ("breaking_news_text", "Welcome to The Crewkerne Gazette - Your trusted source for local news")
        ]
        
        for key, value in settings_defaults:
            setting = db.query(DBSettings).filter(DBSettings.key == key).first()
            if not setting:
                setting = DBSettings(key=key, value=value)
                db.add(setting)
        
        db.commit()
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()