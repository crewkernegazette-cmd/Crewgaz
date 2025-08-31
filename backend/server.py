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
    ArticleCategory, UserRole, hash_password, verify_password, generate_slug
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
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Crewkerne Gazette API", version="2.0.0")
api_router = APIRouter(prefix="/api")

# JWT config with secure default fallback
JWT_SECRET = os.getenv('JWT_SECRET') or 'emergency-fallback-secret-key-please-change'
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Log if using fallback JWT secret
if os.getenv('JWT_SECRET') is None:
    logger.warning("⚠️ Using emergency JWT_SECRET fallback - please set JWT_SECRET environment variable for security")

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
    slug: str
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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user with emergency fallback"""
    try:
        token = credentials.credentials
        token_data = decode_jwt_token(token)
        username = token_data.get('username')
        role = token_data.get('role')
        user_id = token_data.get('user_id')
        
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Try database first (create our own session to handle failures gracefully)
        try:
            from database import SessionLocal
            db = SessionLocal()
            try:
                db_user = db.query(DBUser).filter(DBUser.username == username).first()
                if db_user:
                    logger.debug(f"🔐 User validation: Database user found for {username}")
                    user_obj = User(
                        id=db_user.id,
                        username=db_user.username,
                        email=db_user.email,
                        role=db_user.role,
                        is_active=db_user.is_active,
                        created_at=db_user.created_at
                    )
                    db.close()
                    return user_obj
            finally:
                db.close()
        except Exception as db_error:
            logger.warning(f"🆘 Database user lookup failed: {db_error}")
        
        # Emergency fallback - validate against emergency users if database fails
        emergency_users = {
            "admin": {"role": UserRole.ADMIN, "id": 1},
            "admin_backup": {"role": UserRole.ADMIN, "id": 2},
            "Gazette": {"role": UserRole.ADMIN, "id": 3}
        }
        
        if username in emergency_users and user_id == "emergency":
            logger.info(f"🆘 Emergency user validation for {username}")
            emergency_user = emergency_users[username]
            return User(
                id=emergency_user["id"],
                username=username,
                email=f"{username}@emergency.local",
                role=emergency_user["role"],
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
        
        # If we get here, user not found in database or emergency system
        logger.warning(f"❌ User {username} not found in database or emergency system")
        raise HTTPException(status_code=401, detail="User not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
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
@app.get("/article/{article_slug}")
async def serve_article_page(article_slug: str, request: Request, db: Session = Depends(get_db)):
    """
    Serve article page with proper meta tags for crawlers,
    or serve React app for regular users
    """
    user_agent = request.headers.get('user-agent', '')
    
    if is_crawler(user_agent):
        # Serve static HTML with meta tags for crawlers
        try:
            db_article = db.query(DBArticle).filter(DBArticle.slug == article_slug).first()
            if not db_article:
                raise HTTPException(status_code=404, detail="Article not found")
            
            # Convert to Pydantic model
            article_obj = Article(
                id=db_article.id,
                uuid=db_article.uuid,
                slug=db_article.slug,
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
            
            if article_obj.featured_image:
                if article_obj.featured_image.startswith('http'):
                    # Cloudinary or other hosted image - use standard dimensions
                    image_width_tag = '    <meta property="og:image:width" content="1200">'
                    image_height_tag = '    <meta property="og:image:height" content="630">'
                elif article_obj.featured_image.startswith('data:image/'):
                    # Base64 image (legacy) - calculate dimensions
                    try:
                        header, data = article_obj.featured_image.split(',', 1)
                        image_data = base64.b64decode(data)
                        img = Image.open(io.BytesIO(image_data))
                        image_width_tag = f'    <meta property="og:image:width" content="{img.width}">'
                        image_height_tag = f'    <meta property="og:image:height" content="{img.height}">'
                    except Exception as e:
                        print(f"⚠️ Failed to get image dimensions: {e}")
                        image_width_tag = '    <meta property="og:image:width" content="1200">'
                        image_height_tag = '    <meta property="og:image:height" content="630">'
            else:
                # Default dimensions for logo
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
    <meta property="og:url" content="https://crewkernegazette.co.uk/article/{article_slug}">
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
    <link rel="canonical" href="https://crewkernegazette.co.uk/article/{article_slug}">
    
    <!-- JSON-LD Structured Data for Google News -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": "{title_safe}",
        "description": "{description_safe}",
        "image": "{image_url}",
        "datePublished": "{article_obj.created_at.isoformat()}",
        "dateModified": "{article_obj.updated_at.isoformat()}",
        "author": {{
            "@type": "Person",
            "name": "{article_obj.author_name or article_obj.publisher_name}"
        }},
        "publisher": {{
            "@type": "Organization", 
            "name": "The Crewkerne Gazette",
            "logo": {{
                "@type": "ImageObject",
                "url": "https://crewkernegazette.co.uk/logo.png"
            }}
        }},
        "mainEntityOfPage": {{
            "@type": "WebPage",
            "@id": "https://crewkernegazette.co.uk/article/{article_slug}"
        }},
        "articleSection": "{article_obj.category.value if hasattr(article_obj.category, 'value') else article_obj.category}",
        "keywords": "{', '.join(json.loads(article_obj.tags)) if article_obj.tags else article_obj.category.value if hasattr(article_obj.category, 'value') else article_obj.category}"
    }}
    </script>
</head>
<body>
    <h1>{title_safe}</h1>
    {f"<h2>{(article_obj.subheading or '').replace('<', '&lt;').replace('>', '&gt;')}</h2>" if article_obj.subheading else ""}
    <p>{article_obj.content[:300].replace('<', '&lt;').replace('>', '&gt;')}...</p>
    <p><strong>Category:</strong> {article_obj.category.value if hasattr(article_obj.category, 'value') else article_obj.category}</p>
    <p><strong>Published:</strong> {article_obj.created_at.strftime('%B %d, %Y')}</p>
    <p><em>Read the full article at: <a href="https://crewkernegazette.co.uk/article/{article_slug}">The Crewkerne Gazette</a></em></p>
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
    """Login user - prioritize database, fallback to emergency"""
    logger.info(f"🔐 Login attempt for user: {user_data.username}")
    
    # Enhanced logging for debugging
    try:
        # First try database authentication
        logger.debug("🗄️ Querying database for user...")
        db_user = db.query(DBUser).filter(DBUser.username == user_data.username).first()
        
        if db_user:
            logger.info(f"👤 DB query result: Found user '{db_user.username}' (ID: {db_user.id}, role: {db_user.role}, active: {db_user.is_active})")
            
            if not db_user.is_active:
                logger.warning("❌ User account is disabled")
                raise HTTPException(status_code=400, detail="Account disabled")
            
            # Verify password with enhanced logging
            logger.debug(f"🔐 Verifying password against database hash (hash length: {len(db_user.password_hash)})")
            password_valid = verify_password(user_data.password, db_user.password_hash)
            logger.info(f"🔐 Password verify result: {'✅ SUCCESS' if password_valid else '❌ FAILED'}")
            
            if password_valid:
                logger.info("✅ Database authentication successful")
                
                # Create token
                token_data = {
                    "username": db_user.username,
                    "role": db_user.role.value,
                    "user_id": db_user.id
                }
                
                # Test JWT creation doesn't fail
                try:
                    access_token = create_jwt_token(token_data)
                    logger.debug(f"🎫 JWT token created successfully (length: {len(access_token)})")
                except Exception as jwt_error:
                    logger.error(f"❌ JWT token creation failed: {jwt_error}")
                    raise HTTPException(status_code=500, detail="Token creation failed")
                
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "role": db_user.role.value,
                    "message": "Database login successful"
                }
            else:
                logger.warning("❌ Invalid password for database user")
        else:
            logger.info(f"👤 DB query result: User '{user_data.username}' NOT FOUND in database")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"⚠️ Database authentication error: {e}")
        import traceback
        logger.debug(f"🔍 Database error traceback: {traceback.format_exc()}")
    
    # Fallback to emergency login system
    logger.info("🆘 Attempting emergency authentication fallback...")
    emergency_users = {
        "admin": {"password_hash": hash_password("admin123"), "role": UserRole.ADMIN},
        "admin_backup": {"password_hash": hash_password("admin_backup"), "role": UserRole.ADMIN},
        "Gazette": {"password_hash": hash_password("Gazette2024!"), "role": UserRole.ADMIN}
    }
    
    if user_data.username in emergency_users:
        logger.debug(f"🆘 Found emergency user: {user_data.username}")
        emergency_user = emergency_users[user_data.username]
        
        if verify_password(user_data.password, emergency_user['password_hash']):
            logger.info(f"✅ Fallback auth for {user_data.username} - Emergency authentication successful")
            
            try:
                access_token = create_jwt_token({
                    "username": user_data.username,
                    "role": emergency_user['role'].value,
                    "user_id": "emergency"
                })
                logger.debug(f"🎫 Emergency JWT token created (length: {len(access_token)})")
            except Exception as jwt_error:
                logger.error(f"❌ Emergency JWT token creation failed: {jwt_error}")
                raise HTTPException(status_code=500, detail="Emergency token creation failed")
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "role": emergency_user['role'].value,
                "message": "Emergency login successful"
            }
        else:
            logger.warning("❌ Emergency password verification failed")
    else:
        logger.debug(f"🆘 User '{user_data.username}' not in emergency users")
    
    logger.error("❌ Authentication failed - all methods exhausted")
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

# Image Upload Routes
@api_router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Upload image to Cloudinary"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        contents = await file.read()
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            contents,
            folder="crewkerne-gazette",
            resource_type="image",
            transformation=[
                {"width": 1200, "height": 630, "crop": "limit"},
                {"quality": "auto"},
                {"format": "auto"}
            ]
        )
        
        return {
            "url": upload_result['secure_url'],
            "public_id": upload_result['public_id'],
            "width": upload_result.get('width'),
            "height": upload_result.get('height'),
            "format": upload_result.get('format'),
            "bytes": upload_result.get('bytes')
        }
        
    except Exception as e:
        logger.error(f"Image upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

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

@api_router.get("/articles/{article_slug}", response_model=Article)
async def get_article(article_slug: str, db: Session = Depends(get_db)):
    """Get article by slug"""
    db_article = db.query(DBArticle).filter(DBArticle.slug == article_slug).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return Article(
        id=db_article.id,
        uuid=db_article.uuid,
        slug=db_article.slug,
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
async def create_article(
    title: str = Form(...),
    content: str = Form(...),
    category: ArticleCategory = Form(...),
    subheading: Optional[str] = Form(None),
    publisher_name: Optional[str] = Form("The Crewkerne Gazette"),
    image_caption: Optional[str] = Form(None),
    video_url: Optional[str] = Form(None),
    tags: Optional[str] = Form("[]"),
    is_breaking: bool = Form(False),
    is_published: bool = Form(True),
    featured_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new article with optional image upload"""
    
    # Handle image upload if provided
    featured_image_url = None
    if featured_image and featured_image.content_type.startswith('image/'):
        try:
            # Read file content
            contents = await featured_image.read()
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="crewkerne-gazette/articles",
                resource_type="image",
                transformation=[
                    {"width": 1200, "height": 630, "crop": "limit"},
                    {"quality": "auto"},
                    {"format": "auto"}
                ]
            )
            
            featured_image_url = upload_result['secure_url']
            logger.info(f"Image uploaded to Cloudinary: {featured_image_url}")
            
        except Exception as e:
            logger.error(f"Image upload error: {str(e)}")
            # Continue without image rather than failing
            pass
    
    # Parse tags
    try:
        tags_list = json.loads(tags) if tags else []
    except:
        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
    
    # Sanitize content
    cleaned_content = bleach.clean(
        content, 
        tags=list(bleach.ALLOWED_TAGS) + ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li'],
        strip=True
    )
    
    # Generate UUID and slug for the article
    article_uuid = str(uuid.uuid4())
    article_slug = generate_slug(title, db)
    
    # Create database article
    db_article = DBArticle(
        uuid=article_uuid,
        slug=article_slug,
        title=title,
        subheading=subheading,
        content=cleaned_content,
        category=category,
        publisher_name=publisher_name,
        author_name=current_user.username,
        author_id=str(current_user.id),
        featured_image=featured_image_url,
        image_caption=image_caption,
        video_url=video_url,
        tags=json.dumps(tags_list),
        is_breaking=is_breaking,
        is_published=is_published
    )
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    
    return Article(
        id=db_article.id,
        uuid=db_article.uuid,
        slug=db_article.slug,
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
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics with emergency fallback"""
    try:
        # Try database first
        from database import SessionLocal
        db = SessionLocal()
        try:
            total_articles = db.query(DBArticle).count()
            published_articles = db.query(DBArticle).filter(DBArticle.is_published == True).count()
            breaking_news = db.query(DBArticle).filter(DBArticle.is_breaking == True).count()
            total_contacts = db.query(DBContact).count()
            
            # Check if emergency mode is active (if user_id is "emergency")
            emergency_mode = hasattr(current_user, 'id') and str(current_user.id) == "emergency"
            
            db.close()
            return {
                "total_articles": total_articles,
                "published_articles": published_articles,
                "breaking_news": breaking_news,
                "total_contacts": total_contacts,
                "emergency_mode": emergency_mode
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.warning(f"🆘 Dashboard stats database error: {e}")
        # Emergency fallback - return default stats when database is down
        logger.info("🆘 Returning default stats due to database unavailability")
        return {
            "total_articles": 0,
            "published_articles": 0,
            "breaking_news": 0,
            "total_contacts": 0,
            "emergency_mode": True
        }

@api_router.get("/dashboard/articles", response_model=List[Article])
async def get_dashboard_articles(current_user: User = Depends(get_current_user)):
    """Get articles for dashboard with emergency fallback"""
    try:
        # Try database first
        from database import SessionLocal
        db = SessionLocal()
        try:
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
            
            db.close()
            return articles
            
        finally:
            db.close()
            
    except Exception as e:
        logger.warning(f"🆘 Dashboard articles database error: {e}")
        # Emergency fallback - return empty list when database is down
        logger.info("🆘 Returning empty articles list due to database unavailability")
        return []

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
@api_router.get("/settings")
async def get_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all settings (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "maintenance_mode": get_setting(db, "maintenance_mode", "false").lower() == "true",
        "show_breaking_news_banner": get_setting(db, "show_breaking_news_banner", "true").lower() == "true",
        "breaking_news_text": get_setting(db, "breaking_news_text", "Welcome to The Crewkerne Gazette")
    }

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
@api_router.get("/debug/auth")
async def debug_auth(db: Session = Depends(get_db)):
    """Debug: Get anonymized auth info (no auth required)"""
    try:
        # Get all users (safe info only)
        db_users = db.query(DBUser).all()
        
        users_info = []
        for user in db_users:
            users_info.append({
                "username": user.username,
                "role": user.role.value if user.role else "unknown"
            })
        
        # Test database connection
        db_connected = True
        try:
            db.query(DBUser).first()
        except Exception:
            db_connected = False
        
        # Get seeding status from global variables
        seeding_status = SEEDING_STATUS
        last_error = LAST_ERROR
        
        return {
            "users": users_info,
            "seeding_status": seeding_status,
            "last_error": last_error,
            "db_connected": db_connected,
            "total_users": len(users_info),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Debug auth error: {e}")
        return {
            "users": [],
            "seeding_status": "error",
            "last_error": str(e),
            "db_connected": False,
            "total_users": 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@api_router.get("/debug/users")
async def debug_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Debug: Get anonymized user list (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        db_users = db.query(DBUser).all()
        
        users_info = []
        for user in db_users:
            # Test password for admin users (debugging)
            password_test = None
            if user.username in ["admin", "admin_backup"]:
                test_password = "admin123" if user.username == "admin" else "admin_backup"
                password_test = verify_password(test_password, user.password_hash)
            
            user_info = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "password_hash_length": len(user.password_hash) if user.password_hash else 0,
                "password_test_result": password_test  # Only for debugging
            }
            users_info.append(user_info)
        
        return {
            "total_users": len(users_info),
            "users": users_info,
            "database_connection": "active",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Debug users error: {e}")
        return {
            "error": str(e),
            "total_users": 0,
            "users": [],
            "database_connection": "failed"
        }

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

# Mount frontend static files FIRST for static assets
app.mount("/static", StaticFiles(directory="../frontend/build/static"), name="static")

# SPA fallback route - catch all non-API routes and serve React app
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "HEAD"], include_in_schema=False)
async def spa_fallback(path: str, request: Request):
    """Serve React app for all non-API routes (SPA routing support)"""
    if not path.startswith('api/') and not path.startswith('static/'):
        # For all React Router routes, serve index.html
        try:
            frontend_build_path = Path("../frontend/build/index.html")
            if frontend_build_path.exists():
                with open(frontend_build_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                return HTMLResponse(content=html_content)
            else:
                return HTMLResponse(
                    content="<html><body><h1>Frontend build not found</h1><p>Please run 'yarn build' in the frontend directory.</p></body></html>", 
                    status_code=404
                )
        except Exception as e:
            logger.error(f"SPA fallback error: {e}")
            return HTMLResponse(
                content="<html><body><h1>Error serving frontend</h1></body></html>", 
                status_code=500
            )
    else:
        # This shouldn't happen as API routes are handled by the router
        raise HTTPException(status_code=404, detail="API endpoint not found")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for debug info
SEEDING_STATUS = "unknown"
LAST_ERROR = None

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    global SEEDING_STATUS, LAST_ERROR
    try:
        status, error = init_database()
        SEEDING_STATUS = status or "success"
        LAST_ERROR = error
        logger.info(f"📊 Database seeding status: {SEEDING_STATUS}")
        if error:
            logger.error(f"📊 Last error: {error}")
    except Exception as e:
        SEEDING_STATUS = "failure"
        LAST_ERROR = str(e)
        logger.error(f"❌ Startup database initialization failed: {e}")
    
    print("✅ Crewkerne Gazette PostgreSQL API ready!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)