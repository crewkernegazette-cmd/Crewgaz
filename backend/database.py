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
import re
import unicodedata
from alembic import command
from alembic.config import Config

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database URL from environment variable with SSL support
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://crewkerne_user:crewkerne_pass@localhost/crewkerne_gazette')

# Force-append SSL mode for production (required for Render Postgres)
if DATABASE_URL:
    if '?' not in DATABASE_URL:
        if 'sslmode' not in DATABASE_URL:
            DATABASE_URL += '?sslmode=require'
            logger.info(f"🔒 Force-appended ?sslmode=require to DATABASE_URL")
            # Update environment variable
            os.environ['DATABASE_URL'] = DATABASE_URL
    else:
        if 'sslmode' not in DATABASE_URL:
            DATABASE_URL += '&sslmode=require'
            logger.info(f"🔒 Force-appended &sslmode=require to DATABASE_URL") 
            # Update environment variable
            os.environ['DATABASE_URL'] = DATABASE_URL

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

def generate_slug(title: str, db_session=None) -> str:
    """Generate SEO-friendly slug from article title"""
    # Normalize unicode characters
    slug = unicodedata.normalize('NFKD', title)
    
    # Convert to lowercase and replace spaces with hyphens
    slug = slug.lower().replace(' ', '-')
    
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Truncate to 100 characters
    slug = slug[:100]
    
    # Ensure slug is not empty
    if not slug:
        slug = 'article'
    
    # Check for uniqueness if database session provided
    if db_session:
        original_slug = slug
        counter = 1
        
        while db_session.query(DBArticle).filter(DBArticle.slug == slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
            
            # Prevent infinite loops
            if counter > 1000:
                slug = f"{original_slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                break
    
    logger.info(f"📝 Generated slug: '{title}' -> '{slug}'")
    return slug

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
    uuid = Column(String(36), unique=True, index=True, nullable=False)  # Keep UUID for internal use
    slug = Column(String(255), unique=True, index=True, nullable=False)  # SEO-friendly URL slug
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
    tags = Column(Text, nullable=True)  # JSON string of comma-separated tags
    category_labels = Column(Text, nullable=True)  # JSON string of article category labels
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
    """Create tables and initial data with enhanced seeding"""
    logger.info("🔄 Starting database initialization...")
    seeding_status = "success"
    last_error = None
    
    try:
        # Test database connection first
        with engine.connect() as conn:
            result = conn.execute(text('SELECT 1'))
            logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        seeding_status = "failure"
        last_error = str(e)
        return seeding_status, last_error
    
    try:
        # Create base tables first
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
        
        # Run Alembic migrations to add any new columns/indexes
        try:
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            logger.info("✅ Database migrations applied successfully")
        except Exception as migration_error:
            logger.warning(f"⚠️ Migration warning: {migration_error}")
            # Don't fail completely if migrations have issues
            # This allows the app to work even if migrations can't run
            
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        seeding_status = "failure"
        last_error = str(e)
        return seeding_status, last_error
    
    # Create initial admin user and settings
    db = SessionLocal()
    try:
        # Check existing users
        existing_users_count = db.query(DBUser).count()
        logger.info(f"📊 Existing users in database: {existing_users_count}")
        
        # Handle admin user with force reset capability
        admin_user = db.query(DBUser).filter(DBUser.username == "admin").first()
        
        if admin_user:
            logger.info("👤 Admin user exists, verifying password...")
            # Test current password
            password_valid = verify_password("admin123", admin_user.password_hash)
            
            if not password_valid:
                logger.warning("⚠️ Admin password verification failed, resetting...")
                # Force password reset
                new_hash = hash_password("admin123")
                admin_user.password_hash = new_hash
                admin_user.role = UserRole.ADMIN
                admin_user.is_active = True
                db.commit()
                logger.info("✅ Admin password reset successfully")
                
                # Verify reset worked
                reset_check = verify_password("admin123", admin_user.password_hash)
                logger.info(f"🔐 Password reset verification: {'✅ SUCCESS' if reset_check else '❌ FAILED'}")
            else:
                logger.info("✅ Admin password is valid")
        else:
            logger.info("👤 Creating new admin user...")
            # Create new admin user
            admin_hash = hash_password("admin123")
            admin_user = DBUser(
                username="admin",
                email="admin@crewkernegazette.co.uk",
                password_hash=admin_hash,
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            logger.info("✅ Admin user created successfully")
            
            # Verify creation worked
            creation_check = verify_password("admin123", admin_user.password_hash)
            logger.info(f"🔐 New admin verification: {'✅ SUCCESS' if creation_check else '❌ FAILED'}")
        
        # Handle backup admin user (optional)
        try:
            backup_user = db.query(DBUser).filter(DBUser.username == "admin_backup").first()
            if not backup_user:
                logger.info("👤 Creating backup admin user...")
                backup_hash = hash_password("admin_backup")
                backup_user = DBUser(
                    username="admin_backup", 
                    email="backup@crewkernegazette.co.uk",
                    password_hash=backup_hash,
                    role=UserRole.ADMIN,
                    is_active=True
                )
                db.add(backup_user)
                db.commit()
                logger.info("✅ Backup admin user created")
            else:
                logger.info("✅ Backup admin user already exists")
        except Exception as e:
            logger.warning(f"⚠️ Backup user creation failed (non-critical): {e}")
            
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
        
        # Final verification
        final_user_count = db.query(DBUser).count()
        admin_final = db.query(DBUser).filter(DBUser.username == "admin").first()
        
        logger.info(f"📊 Final user count: {final_user_count}")
        logger.info(f"👤 Admin user ID: {admin_final.id if admin_final else 'NOT FOUND'}")
        logger.info(f"🔐 Admin role: {admin_final.role if admin_final else 'N/A'}")
        logger.info(f"✅ Admin is_active: {admin_final.is_active if admin_final else 'N/A'}")
        
        # Final password test
        if admin_final:
            final_test = verify_password("admin123", admin_final.password_hash)
            logger.info(f"🔐 Final password test: {'✅ PASS' if final_test else '❌ FAIL'}")
            if not final_test:
                logger.error("❌ CRITICAL: Final password test failed!")
        
        # Backfill slugs for existing articles that don't have them
        try:
            articles_without_slugs = db.query(DBArticle).filter(
                (DBArticle.slug.is_(None)) | (DBArticle.slug == '')
            ).all()
            
            if articles_without_slugs:
                logger.info(f"🔄 Backfilling slugs for {len(articles_without_slugs)} articles...")
                
                for article in articles_without_slugs:
                    new_slug = generate_slug(article.title, db)
                    article.slug = new_slug
                    logger.info(f"🏷️ Generated slug for '{article.title}' -> '{new_slug}'")
                
                db.commit()
                logger.info("✅ Slug backfill completed successfully")
            else:
                logger.info("✅ All articles already have slugs")
                
        except Exception as slug_error:
            logger.warning(f"⚠️ Slug backfill warning: {slug_error}")
            # Don't fail the entire initialization if slug backfill has issues
        
        logger.info("✅ Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during database initialization: {e}")
        import traceback
        logger.error(traceback.format_exc())
        seeding_status = "failure"
        last_error = str(e)
        db.rollback()
    finally:
        db.close()
    
    return seeding_status, last_error