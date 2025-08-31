from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Enum as SQLEnum, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
import os
import bcrypt
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database URL from environment variable with SSL support
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://crewkerne_user:crewkerne_pass@localhost/crewkerne_gazette')

# Add SSL mode for production if not present
if DATABASE_URL and 'sslmode=' not in DATABASE_URL:
    ssl_suffix = '?sslmode=require' if '?' not in DATABASE_URL else '&sslmode=require'
    DATABASE_URL_WITH_SSL = DATABASE_URL + ssl_suffix
    logger.info(f"🔒 Added SSL mode to DATABASE_URL")
else:
    DATABASE_URL_WITH_SSL = DATABASE_URL

# Create engine with SSL support and connection arguments
engine = create_engine(
    DATABASE_URL_WITH_SSL,
    connect_args={"sslmode": "require"} if "localhost" not in DATABASE_URL else {},
    echo=False  # Set to True for SQL debugging
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Utility functions for password handling with enhanced bcrypt
from passlib.context import CryptContext

# Initialize password context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using passlib bcrypt context"""
    try:
        hashed = pwd_context.hash(password)
        logger.debug(f"🔐 Password hashed successfully (length: {len(hashed)})")
        return hashed
    except Exception as e:
        logger.error(f"❌ Password hashing failed: {e}")
        # Fallback to manual bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash using passlib"""
    try:
        result = pwd_context.verify(password, password_hash)
        logger.debug(f"🔐 Password verification: {'✅ SUCCESS' if result else '❌ FAILED'}")
        return result
    except Exception as e:
        logger.error(f"❌ Password verification error: {e}")
        # Fallback to manual bcrypt
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e2:
            logger.error(f"❌ Fallback verification failed: {e2}")
            return False

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
        # Check if any users exist first
        existing_users_count = db.query(DBUser).count()
        print(f"📊 Existing users in database: {existing_users_count}")
        
        # Check if admin user exists
        admin_user = db.query(DBUser).filter(DBUser.username == "admin").first()
        if not admin_user:
            print("👤 Creating admin user...")
            admin_user = DBUser(
                username="admin",
                email="admin@crewkernegazette.co.uk",
                password_hash=hash_password("admin123"),
                role=UserRole.ADMIN
            )
            db.add(admin_user)
            print("✅ Admin user created with username: admin, password: admin123")
        else:
            print("✅ Admin user already exists")
        
        # Check if admin_backup user exists
        backup_user = db.query(DBUser).filter(DBUser.username == "admin_backup").first()
        if not backup_user:
            print("👤 Creating backup admin user...")
            backup_user = DBUser(
                username="admin_backup", 
                email="backup@crewkernegazette.co.uk",
                password_hash=hash_password("admin_backup"),
                role=UserRole.ADMIN
            )
            db.add(backup_user)
            print("✅ Backup admin user created")
        else:
            print("✅ Backup admin user already exists")
            
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
        
        # Verify users were created
        final_user_count = db.query(DBUser).count()
        print(f"📊 Total users after initialization: {final_user_count}")
        
        # Test password hashing
        test_admin = db.query(DBUser).filter(DBUser.username == "admin").first()
        if test_admin:
            password_check = verify_password("admin123", test_admin.password_hash)
            print(f"🔐 Password verification test: {'✅ PASS' if password_check else '❌ FAIL'}")
        
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()