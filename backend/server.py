from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Request, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from enum import Enum
import base64
import bleach
from PIL import Image
import io
import json
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Database imports
from sqlalchemy.orm import Session
from database import (
    get_db, init_database, DBArticle, DBContact, DBUser, DBSettings,
    ArticleCategory, UserRole
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'demo'),
    api_key=os.getenv('CLOUDINARY_API_KEY', ''),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', '')
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Crewkerne Gazette API", version="2.0.0")
api_router = APIRouter(prefix="/api")

# JWT config
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Security
security = HTTPBearer()

# Pydantic Models (API Models)
class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER

class LoginRequest(BaseModel):
    username: str
    password: str

class Article(BaseModel):
    id: Optional[int] = None
    uuid: str
    title: str
    subheading: Optional[str] = None
    content: str
    category: ArticleCategory
    publisher_name: str = "The Crewkerne Gazette"
    author_name: Optional[str] = None
    author_id: Optional[str] = None
    featured_image: Optional[str] = None
    image_caption: Optional[str] = None
    video_url: Optional[str] = None
    tags: List[str] = []
    is_breaking: bool = False
    is_published: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    subheading: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=10)
    category: ArticleCategory
    publisher_name: Optional[str] = "The Crewkerne Gazette"
    featured_image: Optional[str] = None
    image_caption: Optional[str] = None
    video_url: Optional[str] = None
    tags: List[str] = []
    is_breaking: bool = False
    is_published: bool = True

    @validator('content', pre=True)
    def sanitize_content(cls, v):
        if v:
            allowed_tags = list(bleach.ALLOWED_TAGS) + ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li']
            return bleach.clean(v, tags=allowed_tags, strip=True)
        return v

class Contact(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    message: str
    created_at: Optional[datetime] = None

class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=10, max_length=1000)

class BreakingNewsBanner(BaseModel):
    show_breaking_news_banner: bool

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class MaintenanceMode(BaseModel):
    maintenance_mode: bool

# Utility Functions
def is_crawler(user_agent: str) -> bool:
    """Detect if the request is from a social media crawler or bot"""
    if not user_agent:
        return False
    
    user_agent_lower = user_agent.lower()
    crawlers = [
        'facebookexternalhit',  # Facebook
        'twitterbot',           # Twitter
        'linkedinbot',          # LinkedIn  
        'whatsapp',             # WhatsApp
        'telegrambot',          # Telegram
        'slackbot',             # Slack
        'discordbot',           # Discord
        'googlebot',            # Google
        'bingbot',              # Bing
        'yandexbot',            # Yandex
        'pinterest',            # Pinterest
        'redditbot',            # Reddit
        'applebot',             # Apple
        'skypeuripreview',      # Skype
        'vkshare',              # VKontakte
        'tumblr',               # Tumblr
        'chatwork'              # ChatWork
    ]
    
    return any(crawler in user_agent_lower for crawler in crawlers)

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_jwt_token(user_data: dict) -> str:
    """Create JWT token"""
    expiry = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    token_data = {**user_data, 'exp': expiry}
    return jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    """Decode JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        token_data = decode_jwt_token(token)
        username = token_data.get('username')
        
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        db_user = db.query(DBUser).filter(DBUser.username == username).first()
        if not db_user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            role=db_user.role,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")

# Helper functions for database operations
def get_setting(db: Session, key: str, default: str = "") -> str:
    """Get setting value from database"""
    setting = db.query(DBSettings).filter(DBSettings.key == key).first()
    return setting.value if setting else default

def set_setting(db: Session, key: str, value: str):
    """Set setting value in database"""
    setting = db.query(DBSettings).filter(DBSettings.key == key).first()
    if setting:
        setting.value = value
        setting.updated_at = datetime.now(timezone.utc)
    else:
        setting = DBSettings(key=key, value=value)
        db.add(setting)
    db.commit()

# Article page route for social media crawlers
@app.get("/article/{article_uuid}")
async def serve_article_page(article_uuid: str, request: Request, db: Session = Depends(get_db)):
    """
    Serve article page with proper meta tags for crawlers,
    or serve React app for regular users
    """
    user_agent = request.headers.get('user-agent', '')
    
    if is_crawler(user_agent):
        # Serve static HTML with meta tags for crawlers
        try:
            db_article = db.query(DBArticle).filter(DBArticle.uuid == article_uuid).first()
            if not db_article:
                raise HTTPException(status_code=404, detail="Article not found")
            
            # Convert to Pydantic model
            article_obj = Article(
                id=db_article.id,
                uuid=db_article.uuid,
                title=db_article.title,
                subheading=db_article.subheading,
                content=db_article.content,
                category=db_article.category,
                publisher_name=db_article.publisher_name,
                author_name=db_article.author_name,
                author_id=db_article.author_id,
                featured_image=db_article.featured_image,
                image_caption=db_article.image_caption,
                video_url=db_article.video_url,
                tags=json.loads(db_article.tags) if db_article.tags else [],
                is_breaking=db_article.is_breaking,
                is_published=db_article.is_published,
                created_at=db_article.created_at,
                updated_at=db_article.updated_at
            )
            
            # Sanitize text content for HTML
            title_safe = article_obj.title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            description_safe = (article_obj.subheading or article_obj.content[:160]).replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            
            # Calculate image dimensions for better social sharing
            image_width_tag = ''
            image_height_tag = ''
            image_url = article_obj.featured_image or 'https://crewkernegazette.co.uk/logo.png'
            
            if article_obj.featured_image and article_obj.featured_image.startswith('data:image/'):
                try:
                    # Extract base64 data
                    header, data = article_obj.featured_image.split(',', 1)
                    image_data = base64.b64decode(data)
                    # Get dimensions with PIL
                    img = Image.open(io.BytesIO(image_data))
                    image_width_tag = f'    <meta property="og:image:width" content="{img.width}">'
                    image_height_tag = f'    <meta property="og:image:height" content="{img.height}">'
                    print(f"📏 Image dimensions calculated: {img.width}x{img.height}")
                except Exception as e:
                    print(f"⚠️ Failed to get image dimensions: {e}")
                    # Fallback to standard social media dimensions
                    image_width_tag = '    <meta property="og:image:width" content="1200">'
                    image_height_tag = '    <meta property="og:image:height" content="630">'
            else:
                # Default dimensions for external images
                image_width_tag = '    <meta property="og:image:width" content="1200">'
                image_height_tag = '    <meta property="og:image:height" content="630">'
            
            # Generate SEO-friendly meta HTML for crawlers
            meta_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Basic Meta Tags -->
    <title>{title_safe} | The Crewkerne Gazette</title>
    <meta name="description" content="{description_safe}">
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="{title_safe}">
    <meta property="og:description" content="{description_safe}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://crewkernegazette.co.uk/article/{article_uuid}">
    <meta property="og:image" content="{image_url}">
{image_width_tag}
{image_height_tag}
    <meta property="og:site_name" content="The Crewkerne Gazette">
    <meta property="article:published_time" content="{article_obj.created_at.isoformat()}">
    <meta property="article:author" content="{article_obj.author_name or article_obj.publisher_name}">
    <meta property="article:section" content="{article_obj.category.value if hasattr(article_obj.category, 'value') else article_obj.category}">
    
    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title_safe}">
    <meta name="twitter:description" content="{description_safe}">
    <meta name="twitter:image" content="{image_url}">
    <meta name="twitter:site" content="@CrewkerneGazette">
    
    <!-- Canonical URL -->
    <link rel="canonical" href="https://crewkernegazette.co.uk/article/{article_uuid}">
</head>
<body>
    <h1>{title_safe}</h1>
    {f"<h2>{(article_obj.subheading or '').replace('<', '&lt;').replace('>', '&gt;')}</h2>" if article_obj.subheading else ""}
    <p>{article_obj.content[:300].replace('<', '&lt;').replace('>', '&gt;')}...</p>
    <p><strong>Category:</strong> {article_obj.category.value if hasattr(article_obj.category, 'value') else article_obj.category}</p>
    <p><strong>Published:</strong> {article_obj.created_at.strftime('%B %d, %Y')}</p>
    <p><em>Read the full article at: <a href="https://crewkernegazette.co.uk/article/{article_uuid}">The Crewkerne Gazette</a></em></p>
</body>
</html>"""
            
            return HTMLResponse(content=meta_html)
            
        except HTTPException:
            raise
        except Exception as e:
            # Error generating meta HTML - return generic 404
            raise HTTPException(status_code=404, detail="Article not found")
    
    else:
        # For regular users, serve the React app's index.html
        try:
            frontend_path = Path("../frontend/build/index.html")
            if frontend_path.exists():
                with open(frontend_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                return HTMLResponse(content=html_content)
            else:
                # Fallback redirect if build not found
                raise HTTPException(
                    status_code=302,
                    headers={"Location": f"/"}
                )
        except Exception:
            # Fallback to homepage
            raise HTTPException(
                status_code=302,
                headers={"Location": f"/"}
            )

# Authentication Routes
@api_router.post("/auth/login")
async def login(user_data: LoginRequest, db: Session = Depends(get_db)):
    """Login user"""
    # Try emergency login first (for backward compatibility)
    emergency_users = {
        "admin": {"password_hash": hash_password("admin123"), "role": UserRole.ADMIN},
        "admin_backup": {"password_hash": hash_password("admin_backup"), "role": UserRole.ADMIN},
        "Gazette": {"password_hash": hash_password("Gazette2024!"), "role": UserRole.ADMIN}
    }
    
    if user_data.username in emergency_users:
        emergency_user = emergency_users[user_data.username]
        if verify_password(user_data.password, emergency_user['password_hash']):
            return {
                "access_token": create_jwt_token({
                    "username": user_data.username,
                    "role": emergency_user['role'].value
                }),
                "token_type": "bearer",
                "role": emergency_user['role'].value
            }
    
    # Try database login
    db_user = db.query(DBUser).filter(DBUser.username == user_data.username).first()
    if db_user and verify_password(user_data.password, db_user.password_hash):
        if not db_user.is_active:
            raise HTTPException(status_code=400, detail="Account disabled")
        
        return {
            "access_token": create_jwt_token({
                "username": db_user.username,
                "role": db_user.role.value
            }),
            "token_type": "bearer",
            "role": db_user.role.value
        }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@api_router.post("/auth/change-password")
async def change_password(password_data: PasswordChangeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Change user password"""
    db_user = db.query(DBUser).filter(DBUser.username == current_user.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(password_data.current_password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    db_user.password_hash = hash_password(password_data.new_password)
    db_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"message": "Password changed successfully"}

# Article Routes
@api_router.get("/articles", response_model=List[Article])
async def get_articles(limit: int = 10, category: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all published articles"""
    query = db.query(DBArticle).filter(DBArticle.is_published == True)
    
    if category:
        query = query.filter(DBArticle.category == category)
    
    db_articles = query.order_by(DBArticle.created_at.desc()).limit(limit).all()
    
    # Convert to Pydantic models
    articles = []
    for db_article in db_articles:
        article = Article(
            id=db_article.id,
            uuid=db_article.uuid,
            title=db_article.title,
            subheading=db_article.subheading,
            content=db_article.content,
            category=db_article.category,
            publisher_name=db_article.publisher_name,
            author_name=db_article.author_name,
            author_id=db_article.author_id,
            featured_image=db_article.featured_image,
            image_caption=db_article.image_caption,
            video_url=db_article.video_url,
            tags=json.loads(db_article.tags) if db_article.tags else [],
            is_breaking=db_article.is_breaking,
            is_published=db_article.is_published,
            created_at=db_article.created_at,
            updated_at=db_article.updated_at
        )
        articles.append(article)
    
    return articles

@api_router.get("/articles/{article_uuid}", response_model=Article)
async def get_article(article_uuid: str, db: Session = Depends(get_db)):
    """Get article by UUID"""
    db_article = db.query(DBArticle).filter(DBArticle.uuid == article_uuid).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return Article(
        id=db_article.id,
        uuid=db_article.uuid,
        title=db_article.title,
        subheading=db_article.subheading,
        content=db_article.content,
        category=db_article.category,
        publisher_name=db_article.publisher_name,
        author_name=db_article.author_name,
        author_id=db_article.author_id,
        featured_image=db_article.featured_image,
        image_caption=db_article.image_caption,
        video_url=db_article.video_url,
        tags=json.loads(db_article.tags) if db_article.tags else [],
        is_breaking=db_article.is_breaking,
        is_published=db_article.is_published,
        created_at=db_article.created_at,
        updated_at=db_article.updated_at
    )

@api_router.post("/articles", response_model=Article)
async def create_article(article_data: ArticleCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create new article"""
    # Generate UUID for the article
    article_uuid = str(uuid.uuid4())
    
    # Create database article
    db_article = DBArticle(
        uuid=article_uuid,
        title=article_data.title,
        subheading=article_data.subheading,
        content=article_data.content,
        category=article_data.category,
        publisher_name=article_data.publisher_name,
        author_name=current_user.username,
        author_id=str(current_user.id),
        featured_image=article_data.featured_image,
        image_caption=article_data.image_caption,
        video_url=article_data.video_url,
        tags=json.dumps(article_data.tags),
        is_breaking=article_data.is_breaking,
        is_published=article_data.is_published
    )
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    return Article(
        id=db_article.id,
        uuid=db_article.uuid,
        title=db_article.title,
        subheading=db_article.subheading,
        content=db_article.content,
        category=db_article.category,
        publisher_name=db_article.publisher_name,
        author_name=db_article.author_name,
        author_id=db_article.author_id,
        featured_image=db_article.featured_image,
        image_caption=db_article.image_caption,
        video_url=db_article.video_url,
        tags=json.loads(db_article.tags) if db_article.tags else [],
        is_breaking=db_article.is_breaking,
        is_published=db_article.is_published,
        created_at=db_article.created_at,
        updated_at=db_article.updated_at
    )

@api_router.put("/articles/{article_uuid}", response_model=Article)
async def update_article(article_uuid: str, article_data: ArticleCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update existing article"""
    db_article = db.query(DBArticle).filter(DBArticle.uuid == article_uuid).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and db_article.author_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only edit your own articles")
    
    # Update fields
    db_article.title = article_data.title
    db_article.subheading = article_data.subheading
    db_article.content = article_data.content
    db_article.category = article_data.category
    db_article.publisher_name = article_data.publisher_name
    db_article.featured_image = article_data.featured_image
    db_article.image_caption = article_data.image_caption
    db_article.video_url = article_data.video_url
    db_article.tags = json.dumps(article_data.tags)
    db_article.is_breaking = article_data.is_breaking
    db_article.is_published = article_data.is_published
    db_article.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(db_article)
    
    return Article(
        id=db_article.id,
        uuid=db_article.uuid,
        title=db_article.title,
        subheading=db_article.subheading,
        content=db_article.content,
        category=db_article.category,
        publisher_name=db_article.publisher_name,
        author_name=db_article.author_name,
        author_id=db_article.author_id,
        featured_image=db_article.featured_image,
        image_caption=db_article.image_caption,
        video_url=db_article.video_url,
        tags=json.loads(db_article.tags) if db_article.tags else [],
        is_breaking=db_article.is_breaking,
        is_published=db_article.is_published,
        created_at=db_article.created_at,
        updated_at=db_article.updated_at
    )

@api_router.delete("/articles/{article_uuid}")
async def delete_article(article_uuid: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete article"""
    db_article = db.query(DBArticle).filter(DBArticle.uuid == article_uuid).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and db_article.author_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only delete your own articles")
    
    db.delete(db_article)
    db.commit()
    
    return {"message": "Article deleted successfully", "deleted_article_uuid": article_uuid}

# Dashboard Routes
@api_router.get("/dashboard/articles", response_model=List[Article])
async def get_dashboard_articles(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get articles for dashboard"""
    if current_user.role == UserRole.ADMIN:
        db_articles = db.query(DBArticle).order_by(DBArticle.created_at.desc()).all()
    else:
        db_articles = db.query(DBArticle).filter(DBArticle.author_id == str(current_user.id)).order_by(DBArticle.created_at.desc()).all()
    
    # Convert to Pydantic models
    articles = []
    for db_article in db_articles:
        article = Article(
            id=db_article.id,
            uuid=db_article.uuid,
            title=db_article.title,
            subheading=db_article.subheading,
            content=db_article.content,
            category=db_article.category,
            publisher_name=db_article.publisher_name,
            author_name=db_article.author_name,
            author_id=db_article.author_id,
            featured_image=db_article.featured_image,
            image_caption=db_article.image_caption,
            video_url=db_article.video_url,
            tags=json.loads(db_article.tags) if db_article.tags else [],
            is_breaking=db_article.is_breaking,
            is_published=db_article.is_published,
            created_at=db_article.created_at,
            updated_at=db_article.updated_at
        )
        articles.append(article)
    
    return articles

# Contact Routes
@api_router.post("/contacts", response_model=Contact)
async def create_contact(contact_data: ContactCreate, db: Session = Depends(get_db)):
    """Create contact message"""
    db_contact = DBContact(
        name=contact_data.name,
        email=contact_data.email,
        message=contact_data.message
    )
    
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    
    return Contact(
        id=db_contact.id,
        name=db_contact.name,
        email=db_contact.email,
        message=db_contact.message,
        created_at=db_contact.created_at
    )

@api_router.get("/contacts", response_model=List[Contact])
async def get_contacts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all contact messages (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db_contacts = db.query(DBContact).order_by(DBContact.created_at.desc()).all()
    
    contacts = []
    for db_contact in db_contacts:
        contact = Contact(
            id=db_contact.id,
            name=db_contact.name,
            email=db_contact.email,
            message=db_contact.message,
            created_at=db_contact.created_at
        )
        contacts.append(contact)
    
    return contacts

# Settings Routes
@api_router.get("/settings/public")
async def get_public_settings(db: Session = Depends(get_db)):
    """Get public settings"""
    return {
        "maintenance_mode": get_setting(db, "maintenance_mode", "false").lower() == "true",
        "show_breaking_news_banner": get_setting(db, "show_breaking_news_banner", "true").lower() == "true",
        "breaking_news_text": get_setting(db, "breaking_news_text", "Welcome to The Crewkerne Gazette")
    }

@api_router.post("/settings/maintenance")
async def toggle_maintenance_mode(maintenance_data: MaintenanceMode, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Toggle maintenance mode"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    set_setting(db, "maintenance_mode", "true" if maintenance_data.maintenance_mode else "false")
    
    status_text = "enabled" if maintenance_data.maintenance_mode else "disabled"
    return {"message": f"Maintenance mode {status_text} successfully"}

@api_router.post("/settings/breaking-news-banner")
async def toggle_breaking_news_banner(banner_data: BreakingNewsBanner, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Toggle breaking news banner"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    set_setting(db, "show_breaking_news_banner", "true" if banner_data.show_breaking_news_banner else "false")
    
    status_text = "enabled" if banner_data.show_breaking_news_banner else "disabled"
    return {"message": f"Breaking news banner {status_text} successfully"}

# Debug and utility routes
@api_router.get("/debug/articles")
async def debug_articles(db: Session = Depends(get_db)):
    """Debug: Get articles info"""
    total_articles = db.query(DBArticle).count()
    recent_articles = db.query(DBArticle).order_by(DBArticle.created_at.desc()).limit(3).all()
    
    sample_article_ids = [article.uuid for article in recent_articles]
    
    return {
        "total_articles": total_articles,
        "sample_article_ids": sample_article_ids,
        "articles": [
            {
                "id": article.id,
                "uuid": article.uuid,
                "title": article.title,
                "category": article.category,
                "is_breaking": article.is_breaking,
                "created_at": article.created_at
            }
            for article in recent_articles
        ]
    }

@api_router.get("/articles/{article_uuid}/structured-data")
async def get_article_structured_data(article_uuid: str, db: Session = Depends(get_db)):
    """Generate structured data for an article"""
    db_article = db.query(DBArticle).filter(DBArticle.uuid == article_uuid).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": db_article.title,
        "description": db_article.subheading or db_article.content[:160],
        "image": db_article.featured_image or "https://crewkernegazette.co.uk/logo.png",
        "datePublished": db_article.created_at.isoformat(),
        "dateModified": db_article.updated_at.isoformat(),
        "author": {
            "@type": "Person",
            "name": db_article.author_name or db_article.publisher_name
        },
        "publisher": {
            "@type": "Organization",
            "name": "The Crewkerne Gazette",
            "logo": {
                "@type": "ImageObject",
                "url": "https://crewkernegazette.co.uk/logo.png"
            }
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"https://crewkernegazette.co.uk/article/{article_uuid}"
        },
        "articleSection": db_article.category.value,
        "keywords": ", ".join(json.loads(db_article.tags)) if db_article.tags else db_article.category.value
    }

# Include router and middleware
app.include_router(api_router)

# Mount frontend static files - this must come AFTER the API routes
# so that our /article/{id} route takes priority over frontend routing
app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="frontend")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    print("✅ Crewkerne Gazette PostgreSQL API ready!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)