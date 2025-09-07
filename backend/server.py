from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Request, Form, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Union
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
import traceback
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Database imports
from sqlalchemy.orm import Session
from database import (
    get_db, init_database, DBArticle, DBContact, DBUser, DBSettings,
    ArticleCategory, UserRole, hash_password, verify_password, generate_slug,
    log_error, ERROR_LOG_BUFFER, coerce_category
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

# Default OG image from environment
DEFAULT_OG_IMAGE = os.getenv("DEFAULT_OG_IMAGE", "https://res.cloudinary.com/dqren9j0f/image/upload/w_1200,h_630,c_fill,f_jpg,q_auto/v123/og-default.jpg")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
FB_APP_ID = os.getenv("FB_APP_ID")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")  # Alternative env var name

# OG image optimization functions
def force_og_image(url: str = None) -> str:
    """Force Cloudinary image to serve as 1200x630 JPEG for scrapers"""
    if not url:
        return DEFAULT_OG_IMAGE
    
    if not url.startswith("http"):
        return DEFAULT_OG_IMAGE
    
    # Ensure Cloudinary serves 1200x630 JPEG for scrapers
    if 'cloudinary.com' in url and '/upload/' in url:
        # Use the correct transform pattern: f_jpg,w_1200,h_630,c_fill,q_auto
        if '/upload/f_jpg,' in url or '/upload/w_' in url:
            # Already has transforms, replace them with our preferred format
            import re
            url = re.sub(r'/upload/[^/]+/', '/upload/f_jpg,w_1200,h_630,c_fill,q_auto/', url)
        else:
            # No transforms, add them with correct order
            url = url.replace("/upload/", "/upload/f_jpg,w_1200,h_630,c_fill,q_auto/")
        return url
    
    # Non-Cloudinary URLs: validate they exist, fallback if not
    try:
        import requests
        response = requests.head(url, timeout=2)
        if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
            return url
    except:
        pass
    
    return DEFAULT_OG_IMAGE

def get_article_by_slug(slug: str, db: Session) -> dict:
    """Get article data optimized for OG tags"""
    try:
        # Normalize slug for case-insensitive lookup
        normalized_slug = slug.strip().lower()
        
        from sqlalchemy import func
        db_article = db.query(DBArticle).filter(func.lower(DBArticle.slug) == normalized_slug).first()
        
        if not db_article:
            return None
            
        # Create excerpt from subheading or content
        excerpt = ""
        if db_article.subheading:
            excerpt = db_article.subheading.strip()[:300]
        elif db_article.content:
            # Strip HTML tags and get plain text excerpt
            import re
            plain_content = re.sub(r'<[^>]+>', '', db_article.content)
            excerpt = plain_content.strip()[:300]
        
        return {
            "title": db_article.title,
            "excerpt": excerpt,
            "heroImageUrl": db_article.featured_image,
            "slug": db_article.slug,
            "id": db_article.id,
            "created_at": db_article.created_at,
            "author_name": db_article.author_name,
            "publisher_name": db_article.publisher_name
        }
    except Exception as e:
        logger.error(f"Error fetching article by slug '{slug}': {e}")
        return None

# Log if using fallback JWT secret
if os.getenv('JWT_SECRET') is None:
    logger.warning("⚠️ Using emergency JWT_SECRET fallback - please set JWT_SECRET environment variable for security")

# Helper functions for OG image handling
def validate_image_url(url, timeout=2):
    """Validate that an image URL returns 200 and proper content-type"""
    try:
        import requests
        response = requests.head(url, timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'})
        content_type = response.headers.get('content-type', '')
        
        return {
            'ok': response.status_code == 200 and content_type.startswith('image/'),
            'status_code': response.status_code,
            'content_type': content_type
        }
    except Exception as e:
        logger.warning(f"Image validation failed for {url}: {str(e)}")
        return {'ok': False, 'status_code': 0, 'content_type': 'error', 'error': str(e)}

def pick_og_image(article_obj):
    """Pick the best available og:image URL with bulletproof validation and fallbacks"""
    
    # Hardcoded safe fallback (guaranteed to exist)
    SAFE_FALLBACK = "https://res.cloudinary.com/dqren9j0f/image/upload/w_1200,h_630,c_fill,f_jpg/crewkerne-gazette/og-default.jpg"
    
    # 1. Try article featured image if available
    if article_obj and article_obj.featured_image and article_obj.featured_image.startswith("http"):
        image_url = article_obj.featured_image
        
        # Enhance Cloudinary URLs without existing transforms
        if ('cloudinary.com' in image_url and '/upload/' in image_url):
            # Check if it already has transforms
            if not any(param in image_url for param in ['f_auto', 'w_', 'h_', 'c_fill']):
                # Insert our transform after /upload/
                image_url = image_url.replace('/upload/', '/upload/f_auto,q_auto,w_1200,h_630,c_fill,f_jpg/')
                logger.info(f"🖼️ Enhanced Cloudinary image: {image_url}")
            else:
                # Force JPEG format for existing transforms
                if 'f_' not in image_url:
                    image_url = image_url.replace('/upload/', '/upload/f_jpg/')
                logger.info(f"🖼️ Using enhanced article image: {image_url}")
        
        # Validate the URL
        validation = validate_image_url(image_url)
        if validation['ok']:
            logger.info(f"🖼️ Validated article featured image: {image_url}")
            return image_url
        else:
            logger.warning(f"🖼️ Article image validation failed: {validation}")
    
    # 2. Try DEFAULT_OG_IMAGE from environment
    if DEFAULT_OG_IMAGE and DEFAULT_OG_IMAGE.startswith("http"):
        validation = validate_image_url(DEFAULT_OG_IMAGE)
        if validation['ok']:
            logger.info(f"🖼️ Using validated DEFAULT_OG_IMAGE: {DEFAULT_OG_IMAGE}")
            return DEFAULT_OG_IMAGE
        else:
            logger.warning(f"🖼️ DEFAULT_OG_IMAGE validation failed: {validation}")
    
    # 3. Last resort: hardcoded safe fallback
    logger.info(f"🖼️ Using hardcoded safe fallback: {SAFE_FALLBACK}")
    return SAFE_FALLBACK

def absolutize(url):
    """Ensure URL is absolute HTTPS"""
    return url if url.startswith("http") else f"https://crewkernegazette.co.uk{url}"

def calculate_levenshtein_distance(s1, s2):
    """Calculate Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return calculate_levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

# Startup self-check for DEFAULT_OG_IMAGE
try:
    if DEFAULT_OG_IMAGE:
        validation = validate_image_url(DEFAULT_OG_IMAGE, timeout=5)
        if validation['ok']:
            logger.info(f"✅ DEFAULT_OG_IMAGE startup check: PASSED - {DEFAULT_OG_IMAGE}")
            logger.info(f"   Status: {validation['status_code']}, Content-Type: {validation['content_type']}")
        else:
            logger.error(f"❌ DEFAULT_OG_IMAGE startup check: FAILED - {DEFAULT_OG_IMAGE}")
            logger.error(f"   Status: {validation.get('status_code', 0)}, Content-Type: {validation.get('content_type', 'unknown')}")
    else:
        logger.warning("⚠️ DEFAULT_OG_IMAGE not set in environment")
except Exception as e:
    logger.error(f"❌ DEFAULT_OG_IMAGE startup check error: {str(e)}")

# Cloudinary configuration self-check (mask secrets)
cloudinary_cloud = os.getenv('CLOUDINARY_CLOUD_NAME', 'not_set')
cloudinary_key = os.getenv('CLOUDINARY_API_KEY', 'not_set')
cloudinary_secret = os.getenv('CLOUDINARY_API_SECRET', 'not_set')

logger.info(f"🔧 Cloudinary config: cloud={cloudinary_cloud}, key={'*' * (len(cloudinary_key) - 4) + cloudinary_key[-4:] if len(cloudinary_key) > 4 else 'not_set'}, secret={'SET' if cloudinary_secret != 'not_set' else 'NOT_SET'}")

# Available article categories
AVAILABLE_CATEGORY_LABELS = [
    'Satire', 'Straight Talking', 'Opinion', 'Sports', 'Gossip', 
    'Politics', 'Local News', 'News', 'Agony Aunt', 'Special', 
    'Exclusive', 'Breaking', 'Analysis', 'Interview', 'Review',
    'Investigative', 'Community', 'Business', 'Crime', 'Education'
]

# Security
security = HTTPBearer(auto_error=False)

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

def set_auth_cookie(resp: Response, token: str):
    """Set auth cookie with cross-subdomain configuration"""
    resp.set_cookie(
        key="auth",
        value=token,
        httponly=True,
        secure=True,                        # required when SameSite=None
        samesite="none",
        domain=".crewkernegazette.co.uk",   # leading dot works for root + api subdomain
        path="/",
        max_age=60*60*24*7                  # 7 days
    )

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
    category_labels: List[str] = []  # New field for article category labels
    is_breaking: bool = False
    is_published: bool = True
    pinned_at: Optional[datetime] = None
    priority: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    subheading: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=10)
    category: str  # Accept string, validate in endpoint
    publisher_name: Optional[str] = "The Crewkerne Gazette"
    featured_image: Optional[str] = None
    image_caption: Optional[str] = None
    video_url: Optional[str] = None
    tags: List[str] = []
    category_labels: List[str] = []  # New field for article category labels
    is_breaking: bool = False
    is_published: bool = True
    pin: Optional[bool] = False  # Frontend boolean for pinning
    priority: int = 0



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
    email: str = Field(..., min_length=5, max_length=100)  # Changed from EmailStr to str for now
    message: str = Field(..., min_length=1, max_length=2000)  # Increased length and reduced min

class LeaderboardEntry(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=20)
    score: int = Field(..., ge=0)
    title: str = Field(..., max_length=100)

class LeaderboardResponse(BaseModel):
    scores: List[dict]
    message: str = "Leaderboard retrieved successfully"

@api_router.post("/leaderboard")
async def submit_score(entry: LeaderboardEntry, db: Session = Depends(get_db)):
    """Submit a score to the Dover Dash leaderboard"""
    try:
        # Sanitize player name
        clean_name = bleach.clean(entry.player_name, strip=True)
        clean_title = bleach.clean(entry.title, strip=True)
        
        # Use MongoDB for leaderboard storage
        from pymongo import MongoClient
        import os
        
        # Get MongoDB connection
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
        client = MongoClient(mongo_url)
        db_name = os.getenv('DB_NAME', 'test_database')
        mongo_db = client[db_name]
        
        # Create leaderboard entry
        leaderboard_entry = {
            "player_name": clean_name,
            "score": entry.score,
            "title": clean_title,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Insert into MongoDB
        result = mongo_db.leaderboard.insert_one(leaderboard_entry)
        
        logger.info(f"Dover Dash score submitted: {clean_name} - {entry.score} points")
        
        return {"message": "Score submitted successfully", "ok": True}
        
    except Exception as e:
        logger.error(f"Error submitting Dover Dash score: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit score")

@api_router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(weekly: bool = False, limit: int = 10, db: Session = Depends(get_db)):
    """Get Dover Dash leaderboard scores"""
    try:
        # Ensure the leaderboard table exists
        from sqlalchemy import text
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                id SERIAL PRIMARY KEY,
                player_name VARCHAR(255) NOT NULL,
                score INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Build query
        if weekly:
            # Get scores from last 7 days
            query = text("""
                SELECT player_name, score, title, created_at
                FROM leaderboard 
                WHERE created_at >= NOW() - INTERVAL '7 days'
                ORDER BY score DESC 
                LIMIT :limit
            """)
        else:
            # Get all-time top scores
            query = text("""
                SELECT player_name, score, title, created_at
                FROM leaderboard 
                ORDER BY score DESC 
                LIMIT :limit
            """)
        
        result = db.execute(query, {"limit": limit})
        scores = []
        
        for row in result:
            scores.append({
                "player_name": row[0],
                "score": row[1],
                "title": row[2],
                "created_at": row[3].isoformat() if row[3] else None
            })
        
        message = f"{'Weekly' if weekly else 'All-time'} top {len(scores)} scores retrieved"
        
        return LeaderboardResponse(scores=scores, message=message)
        
    except Exception as e:
        logger.error(f"Error retrieving Dover Dash leaderboard: {e}")
        # Return empty leaderboard instead of error to keep game playable
        return LeaderboardResponse(scores=[], message="Leaderboard temporarily unavailable")

# Mount the Dover Dash game file
@app.get("/dover-dash")
async def serve_dover_dash():
    """Serve the Dover Dash game"""
    try:
        game_path = Path("../frontend/public/dover-dash.html")
        if game_path.exists():
            with open(game_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        else:
            return HTMLResponse(
                content="<html><body><h1>Dover Dash Not Found</h1><p>Game file not available.</p></body></html>", 
                status_code=404
            )
    except Exception as e:
        logger.error(f"Error serving Dover Dash: {e}")
        return HTMLResponse(
            content="<html><body><h1>Error Loading Dover Dash</h1></body></html>", 
            status_code=500
        )

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
    
    # Comprehensive crawler detection patterns
    crawlers = [
        'facebookexternalhit/1.1',                    # Facebook specific
        'facebookexternalhit',                        # Facebook general
        'twitterbot/1.0',                            # Twitter specific
        'twitterbot',                                # Twitter general
        'linkedinbot',                               # LinkedIn
        'whatsapp',                                  # WhatsApp
        'telegrambot',                               # Telegram
        'slackbot',                                  # Slack
        'discordbot',                                # Discord
        'googlebot',                                 # Google
        'bingbot',                                   # Bing
        'yandexbot',                                 # Yandex
        'pinterest',                                 # Pinterest
        'redditbot',                                 # Reddit
        'applebot',                                  # Apple
        'skypeuripreview',                          # Skype
        'vkshare',                                   # VKontakte
        'tumblr',                                    # Tumblr
        'chatwork',                                  # ChatWork
        'msnbot',                                    # MSN Bot
        'ia_archiver',                               # Internet Archive
        'screaming frog',                            # SEO Tools
        'spider',                                    # Generic spiders
        'crawler',                                   # Generic crawlers
        'bot'                                        # Generic bots
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

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """
    Accept auth from either:
      - Authorization: Bearer <JWT>
      - HttpOnly cookie: auth=<JWT>
    """
    token = None

    # 1) Prefer Authorization header if present
    if credentials and credentials.scheme and credentials.scheme.lower() == "bearer":
        token = credentials.credentials

    # 2) Otherwise fall back to cookie
    if not token:
        token = request.cookies.get("auth")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Continue with existing token validation logic
    try:
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

@app.get("/og/article/{slug}")
@app.head("/og/article/{slug}")
async def og_article(slug: str, db: Session = Depends(get_db)):
    """
    Dedicated OG endpoint for social media crawlers.
    Returns HTML with OG meta tags and meta-refresh to canonical SPA URL.
    """
    import html
    
    canonical = f"https://crewkernegazette.co.uk/article/{html.escape(slug)}"
    
    # Try to get article data
    article = get_article_by_slug(slug, db)
    
    if not article:
        logger.info(f"🔗 OG endpoint: Article not found for slug '{slug}', serving 200 OK with default OG tags")
        
        doc = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <title>Article Not Found | The Crewkerne Gazette</title>
    <link rel="canonical" href="{canonical}"/>
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:type" content="article"/>
    <meta property="og:title" content="Article Not Found | The Crewkerne Gazette"/>
    <meta property="og:description" content="This article does not exist on The Crewkerne Gazette."/>
    <meta property="og:url" content="{canonical}"/>
    <meta property="og:image" content="{DEFAULT_OG_IMAGE}"/>
    <meta property="og:image:width" content="1200"/>
    <meta property="og:image:height" content="630"/>
    <meta property="og:site_name" content="The Crewkerne Gazette"/>
    
    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image"/>
    <meta name="twitter:title" content="Article Not Found | The Crewkerne Gazette"/>
    <meta name="twitter:description" content="This article does not exist on The Crewkerne Gazette."/>
    <meta name="twitter:image" content="{DEFAULT_OG_IMAGE}"/>
    
    <!-- Redirect humans to the SPA -->
    <meta http-equiv="refresh" content="0; url={canonical}" />
</head>
<body>
    <h1>Redirecting...</h1>
    <p>If you are not redirected automatically, <a href="{canonical}">click here</a>.</p>
</body>
</html>"""
        # CRITICAL: Return 200 OK, not 404 - Facebook requires 200 to parse OG tags
        return Response(
            doc, 
            media_type="text/html", 
            status_code=200,
            headers={
                "Cache-Control": "public, max-age=300",
                "X-Robots-Tag": "all",
                "Vary": "User-Agent"
            }
        )
    
    # Article found - generate rich OG tags
    title = html.escape(article.get("title") or "The Crewkerne Gazette")
    desc = html.escape((article.get("excerpt") or "").strip()[:300])
    img = force_og_image(article.get("heroImageUrl"))
    author = html.escape(article.get("author_name") or article.get("publisher_name") or "The Crewkerne Gazette")
    
    logger.info(f"🔗 OG endpoint: Serving rich preview for '{title}' with image: {img}")
    
    doc = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <title>{title} | The Crewkerne Gazette</title>
    <link rel="canonical" href="{canonical}"/>
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:type" content="article"/>
    <meta property="og:title" content="{title}"/>
    <meta property="og:description" content="{desc}"/>
    <meta property="og:url" content="{canonical}"/>
    <meta property="og:image" content="{img}"/>
    <meta property="og:image:width" content="1200"/>
    <meta property="og:image:height" content="630"/>
    <meta property="og:site_name" content="The Crewkerne Gazette"/>
    <meta property="article:author" content="{author}"/>
    
    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image"/>
    <meta name="twitter:title" content="{title}"/>
    <meta name="twitter:description" content="{desc}"/>
    <meta name="twitter:image" content="{img}"/>
    <meta name="twitter:site" content="@CrewkerneGazette"/>
    
    <!-- Redirect humans to the SPA (instant redirect) -->
    <meta http-equiv="refresh" content="0; url={canonical}" />
</head>
<body>
    <h1>Redirecting to {title}...</h1>
    <p>If you are not redirected automatically, <a href="{canonical}">click here</a>.</p>
</body>
</html>"""
    
    return Response(
        doc, 
        media_type="text/html", 
        status_code=200,
        headers={
            "Cache-Control": "public, max-age=300",
            "X-Robots-Tag": "all",
            "Vary": "User-Agent"
        }
    )

@app.get("/test/create-sample-article")
async def create_sample_article(db: Session = Depends(get_db)):
    """Create a sample article for testing Facebook sharing"""
    try:
        # Check if sample article already exists
        existing = db.query(DBArticle).filter(DBArticle.slug == "sample-facebook-test-article").first()
        if existing:
            return {
                "message": "Sample article already exists",
                "slug": existing.slug,
                "title": existing.title,
                "og_url": f"https://api.crewkernegazette.co.uk/og/article/{existing.slug}"
            }
        
        # Create sample article
        sample_article = DBArticle(
            uuid=str(uuid.uuid4()),
            slug="sample-facebook-test-article",
            title="Facebook Sharing Test Article",
            subheading="This article tests Facebook Open Graph sharing functionality",
            content="<p>This is a sample article created to test Facebook sharing and Open Graph meta tags. The article contains rich content that should display properly when shared on social media platforms.</p><p>The featured image should appear as a large preview, and the title and description should be correctly formatted for social media sharing.</p>",
            category=ArticleCategory.NEWS,
            publisher_name="The Crewkerne Gazette",
            author_name="Test Author",
            author_id="test-author-123",
            featured_image="https://res.cloudinary.com/demo/image/upload/w_1200,h_630,c_fill,f_jpg,q_auto/sample.jpg",
            image_caption="Sample image for Facebook sharing test",
            tags='["facebook", "sharing", "test", "og-tags"]',
            category_labels='["News", "Tech"]',
            is_breaking=False,
            is_published=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(sample_article)
        db.commit()
        db.refresh(sample_article)
        
        return {
            "message": "Sample article created successfully",
            "slug": sample_article.slug,
            "title": sample_article.title,
            "og_url": f"https://api.crewkernegazette.co.uk/og/article/{sample_article.slug}",
            "share_url": f"https://www.facebook.com/sharer/sharer.php?u=https://api.crewkernegazette.co.uk/og/article/{sample_article.slug}"
        }
        
    except Exception as e:
        logger.error(f"Error creating sample article: {e}")
        return {"error": str(e), "message": "Failed to create sample article"}

# Article page route for social media crawlers (LEGACY - to be phased out)  
@app.get("/article/{article_slug}")
async def serve_article_page(article_slug: str, request: Request, db: Session = Depends(get_db)):
    """
    Serve article page with proper meta tags for crawlers,
    or serve React app for regular users
    """
    user_agent = request.headers.get('user-agent', '')
    
    logger.info(f"🕷️ Request for article '{article_slug}' from User-Agent: {user_agent}")
    
    if is_crawler(user_agent):
        logger.info(f"🤖 Detected crawler for article '{article_slug}', serving meta HTML")
        # Serve static HTML with meta tags for crawlers
        try:
            # HARDENED SLUG LOOKUP - normalize incoming slug
            original_slug = article_slug
            normalized_slug = article_slug.strip().lower()
            
            logger.info(f"🔍 Crawler lookup: original='{original_slug}' normalized='{normalized_slug}'")
            
            # Get recent slugs for comparison (increased to 20 for better debugging)
            recent_articles = db.query(DBArticle).order_by(DBArticle.created_at.desc()).limit(20).all()
            recent_slugs = [art.slug for art in recent_articles]
            logger.info(f"📊 Last 20 slugs in DB: {recent_slugs}")
            
            # Case-insensitive slug lookup
            from sqlalchemy import func
            db_article = db.query(DBArticle).filter(func.lower(DBArticle.slug) == normalized_slug).first()
            
            if not db_article:
                logger.warning(f"📄 Article not found for slug: original='{original_slug}' normalized='{normalized_slug}'")
                
                # Find closest matching slug using Levenshtein distance
                all_slugs = [art.slug for art in db.query(DBArticle).all()]
                closest_matches = []
                for slug in all_slugs:
                    distance = calculate_levenshtein_distance(normalized_slug, slug.lower())
                    closest_matches.append((slug, distance))
                
                closest_matches.sort(key=lambda x: x[1])
                closest_slug = closest_matches[0][0] if closest_matches else "no-articles-found"
                logger.info(f"🎯 Closest slug match: '{closest_slug}' (distance: {closest_matches[0][1] if closest_matches else 'N/A'})")
                
                # Return 200 HTML with default meta tags for non-existent articles
                # This prevents "Bad Response Code" in Facebook debugger
                fallback_image = pick_og_image(None)
                
                # Get Facebook App ID for fallback
                fb_app_id = FACEBOOK_APP_ID or FB_APP_ID
                fb_app_id_tag = f'    <meta property="fb:app_id" content="{fb_app_id}">' if fb_app_id else ""
                
                default_meta_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Basic Meta Tags -->
    <title>Article Not Found | The Crewkerne Gazette</title>
    <meta name="description" content="The requested article could not be found on The Crewkerne Gazette.">
    
    <!-- Open Graph Meta Tags - Complete Set -->
    <meta property="og:title" content="Article Not Found | The Crewkerne Gazette">
    <meta property="og:description" content="The requested article could not be found.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://crewkernegazette.co.uk/article/{article_slug}">
    <meta property="og:image" content="{fallback_image}">
    <meta property="og:image:secure_url" content="{fallback_image}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:type" content="image/jpeg">
    <meta property="og:site_name" content="The Crewkerne Gazette">
{fb_app_id_tag}
    
    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Article Not Found | The Crewkerne Gazette">
    <meta name="twitter:description" content="The requested article could not be found.">
    <meta name="twitter:image" content="{fallback_image}">
    <meta name="twitter:site" content="@CrewkerneGazette">
    
    <!-- Canonical URL -->
    <link rel="canonical" href="https://crewkernegazette.co.uk/">
</head>
<body>
    <h1>Article Not Found</h1>
    <p>The requested article could not be found. Please check the URL or visit our <a href="https://crewkernegazette.co.uk/">homepage</a>.</p>
</body>
</html>"""
                return HTMLResponse(
                    content=default_meta_html, 
                    status_code=200,
                    headers={
                        "Accept-Ranges": "none",
                        "Cache-Control": "public, max-age=300",
                        "X-Robots-Tag": "all",
                        "Vary": "User-Agent",
                        "X-Debug-Slug": normalized_slug,
                        "X-Debug-Closest-Slug": closest_slug
                    }
                )
            
            logger.info(f"✅ Article found: '{db_article.title}' (ID: {db_article.id})")
            
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
                category_labels=json.loads(db_article.category_labels) if db_article.category_labels else [],
                is_breaking=db_article.is_breaking,
                is_published=db_article.is_published,
                pinned_at=db_article.pinned_at,
                priority=db_article.priority,
                created_at=db_article.created_at,
                updated_at=db_article.updated_at
            )
            
            # Sanitize text content for HTML
            title_safe = article_obj.title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            
            # Create safe description - use subheading first, then content excerpt, with proper sanitization
            if article_obj.subheading:
                description_safe = article_obj.subheading[:160].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            else:
                # Strip HTML tags and get plain text excerpt from content
                import re
                plain_content = re.sub(r'<[^>]+>', '', article_obj.content or '')
                description_safe = plain_content[:160].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            
            # Safe timestamp handling - use created_at as fallback for updated_at
            current_time = datetime.now(timezone.utc)
            updated_iso = (article_obj.updated_at or article_obj.created_at or current_time).isoformat()
            published_iso = (article_obj.created_at or current_time).isoformat()
            
            # Use proper Cloudinary image
            image_url = pick_og_image(article_obj)
            
            # Get Facebook App ID for meta tag
            fb_app_id = FACEBOOK_APP_ID or FB_APP_ID
            fb_app_id_tag = f'    <meta property="fb:app_id" content="{fb_app_id}">' if fb_app_id else ""
            
            # Generate OG meta tags with complete, validated values
            meta_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Basic Meta Tags -->
    <title>{title_safe} | The Crewkerne Gazette</title>
    <meta name="description" content="{description_safe}">
    
    <!-- Open Graph Meta Tags - Complete Set -->
    <meta property="og:title" content="{title_safe}">
    <meta property="og:description" content="{description_safe}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://crewkernegazette.co.uk/article/{article_slug}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:image:secure_url" content="{image_url}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:type" content="image/jpeg">
    <meta property="og:site_name" content="The Crewkerne Gazette">
    <meta property="article:published_time" content="{published_iso}">
    <meta property="article:modified_time" content="{updated_iso}">
    <meta property="article:author" content="{article_obj.author_name or article_obj.publisher_name}">
    <meta property="article:section" content="{article_obj.category.value if hasattr(article_obj.category, 'value') else article_obj.category}">
{fb_app_id_tag}
    
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
        "datePublished": "{published_iso}",
        "dateModified": "{updated_iso}",
        "author": {{
            "@type": "Person",
            "name": "{article_obj.author_name or article_obj.publisher_name}"
        }},
        "publisher": {{
            "@type": "Organization", 
            "name": "The Crewkerne Gazette",
            "logo": {{
                "@type": "ImageObject",
                "url": "{image_url}"
            }}
        }},
        "mainEntityOfPage": {{
            "@type": "WebPage",
            "@id": "https://crewkernegazette.co.uk/article/{article_slug}"
        }},
        "articleSection": "{article_obj.category.value if hasattr(article_obj.category, 'value') else article_obj.category}",
        "keywords": "{', '.join(article_obj.tags) if article_obj.tags else (article_obj.category.value if hasattr(article_obj.category, 'value') else str(article_obj.category))}"
    }}
    </script>
</head>
<body>
    <h1>{title_safe}</h1>
    {f"<h2>{(article_obj.subheading or '').replace('<', '&lt;').replace('>', '&gt;')}</h2>" if article_obj.subheading else ""}
    <p>{article_obj.content[:300].replace('<', '&lt;').replace('>', '&gt;')}...</p>
    <p><strong>Category:</strong> {article_obj.category.value if hasattr(article_obj.category, 'value') else article_obj.category}</p>
    <p><strong>Published:</strong> {article_obj.created_at.strftime('%B %d, %Y') if article_obj.created_at else 'Recently'}</p>
    <p><em>Read the full article at: <a href="https://crewkernegazette.co.uk/article/{article_slug}">The Crewkerne Gazette</a></em></p>
</body>
</html>"""
            
            return HTMLResponse(
                content=meta_html, 
                status_code=200,
                headers={
                    "Accept-Ranges": "none",
                    "Cache-Control": "public, max-age=300",
                    "X-Robots-Tag": "all",
                    "Vary": "User-Agent",
                    "X-Debug-Slug": normalized_slug
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error generating article meta HTML for crawler: {e}")
            # For crawlers, ALWAYS return 200 HTML even on database errors
            fallback_image = pick_og_image(None)
            fb_app_id = FACEBOOK_APP_ID or FB_APP_ID
            fb_app_id_tag = f'    <meta property="fb:app_id" content="{fb_app_id}">' if fb_app_id else ""
            
            fallback_meta_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Basic Meta Tags -->
    <title>The Crewkerne Gazette - Where Common Sense Meets Headlines</title>
    <meta name="description" content="Bold, unapologetic journalism from Somerset to the nation.">
    
    <!-- Open Graph Meta Tags - Complete Set -->
    <meta property="og:title" content="The Crewkerne Gazette">
    <meta property="og:description" content="Bold, unapologetic journalism from Somerset to the nation.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://crewkernegazette.co.uk/article/{article_slug}">
    <meta property="og:image" content="{fallback_image}">
    <meta property="og:image:secure_url" content="{fallback_image}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:type" content="image/jpeg">
    <meta property="og:site_name" content="The Crewkerne Gazette">
{fb_app_id_tag}
    
    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="The Crewkerne Gazette">
    <meta name="twitter:description" content="Bold, unapologetic journalism from Somerset to the nation.">
    <meta name="twitter:image" content="{fallback_image}">
    <meta name="twitter:site" content="@CrewkerneGazette">
    
    <!-- JSON-LD Structured Data -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": "The Crewkerne Gazette",
        "description": "Bold, unapologetic journalism from Somerset to the nation.",
        "image": "{fallback_image}",
        "publisher": {{
            "@type": "Organization", 
            "name": "The Crewkerne Gazette",
            "logo": {{
                "@type": "ImageObject",
                "url": "{fallback_image}"
            }}
        }},
        "mainEntityOfPage": {{
            "@type": "WebPage",
            "@id": "https://crewkernegazette.co.uk/article/{article_slug}"
        }}
    }}
    </script>
</head>
<body>
    <h1>The Crewkerne Gazette</h1>
    <p>Bold, unapologetic journalism from Somerset to the nation.</p>
    <p><em>Visit us at: <a href="https://crewkernegazette.co.uk/">The Crewkerne Gazette</a></em></p>
</body>
</html>"""
            return HTMLResponse(
                content=fallback_meta_html, 
                status_code=200,
                headers={
                    "Accept-Ranges": "none",
                    "Cache-Control": "public, max-age=300",
                    "X-Robots-Tag": "all",
                    "Vary": "User-Agent",
                    "X-Debug-Slug": article_slug.strip().lower()
                }
            )
    
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

@app.head("/article/{article_slug}")
async def serve_article_head(article_slug: str, request: Request, db: Session = Depends(get_db)):
    """
    HEAD handler for article pages - returns same headers as GET would for crawlers
    Always returns 200 OK with proper headers, never 206/302/404 for crawlers
    """
    user_agent = request.headers.get('user-agent', '')
    
    if is_crawler(user_agent):
        logger.info(f"🤖 HEAD request from crawler for article '{article_slug}'")
        
        # Normalize slug for debug header
        normalized_slug = article_slug.strip().lower()
        
        # Return 200 with complete headers matching GET response
        return HTMLResponse(
            content="", 
            status_code=200, 
            headers={
                "Accept-Ranges": "none",
                "Cache-Control": "public, max-age=300",
                "X-Robots-Tag": "all",
                "Vary": "User-Agent",
                "Content-Type": "text/html; charset=utf-8",
                "X-Debug-Slug": normalized_slug
            }
        )
    else:
        # For regular users, return basic 200 headers
        return HTMLResponse(
            content="", 
            status_code=200,
            headers={"Content-Type": "text/html; charset=utf-8"}
        )

# CORS preflight handler for article endpoints
@app.options("/api/articles/{path:path}")
async def article_options(path: str):
    """Handle OPTIONS preflight requests for article endpoints"""
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true"
        }
    )

# Authentication Routes
@api_router.post("/auth/login")
async def login(user_data: LoginRequest, response: Response, db: Session = Depends(get_db)):
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
                
                # Set auth cookie
                set_auth_cookie(response, access_token)
                
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
            
            # Set auth cookie
            set_auth_cookie(response, access_token)
            
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
@api_router.get("/categories/labels")
async def get_available_category_labels():
    """Get available category labels for articles"""
    return {"category_labels": AVAILABLE_CATEGORY_LABELS}

@api_router.get("/top-rail")
async def get_top_rail(db: Session = Depends(get_db)):
    """Get articles formatted for GB News-style top rail layout"""
    try:
        # Get articles with the same ordering logic as main listing
        query = db.query(DBArticle).filter(DBArticle.is_published == True)
        
        db_articles = query.order_by(
            (DBArticle.pinned_at.isnot(None)).desc(),
            DBArticle.pinned_at.desc(),
            DBArticle.priority.desc(),
            DBArticle.is_breaking.desc(),
            DBArticle.created_at.desc()
        ).limit(15).all()
        
        articles = []
        for db_article in db_articles:
            article = Article(
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
                category_labels=json.loads(db_article.category_labels) if db_article.category_labels else [],
                is_breaking=db_article.is_breaking,
                is_published=db_article.is_published,
                pinned_at=db_article.pinned_at,
                priority=db_article.priority,
                created_at=db_article.created_at,
                updated_at=db_article.updated_at
            )
            articles.append(article)
        
        # Format for top rail layout
        return {
            "lead": articles[0] if articles else None,
            "secondary": articles[1:4] if len(articles) > 1 else [],
            "more": articles[4:] if len(articles) > 4 else []
        }
        
    except Exception as e:
        error_msg = f"Failed to fetch top rail: {str(e)}"
        log_error(error_msg, e)
        raise HTTPException(status_code=500, detail={
            "ok": False,
            "error": "Failed to load top rail content",
            "details": {"message": str(e)}
        })

@api_router.get("/articles", response_model=List[Article])
async def get_articles(limit: int = 10, category: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all published articles"""
    query = db.query(DBArticle).filter(DBArticle.is_published == True)
    
    if category:
        query = query.filter(DBArticle.category == category)
    
    # Order by pinning logic: pinned first, then by priority, breaking, then newest
    db_articles = query.order_by(
        (DBArticle.pinned_at.isnot(None)).desc(),  # Pinned articles first
        DBArticle.pinned_at.desc(),                # Newest pin wins among pinned
        DBArticle.priority.desc(),                 # Higher priority first
        DBArticle.is_breaking.desc(),              # Breaking news next
        DBArticle.created_at.desc()                # Then by newest
    ).limit(limit).all()
    
    # Convert to Pydantic models
    articles = []
    for db_article in db_articles:
        article = Article(
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
            category_labels=json.loads(db_article.category_labels) if db_article.category_labels else [],
            is_breaking=db_article.is_breaking,
            is_published=db_article.is_published,
            pinned_at=db_article.pinned_at,
            priority=db_article.priority,
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
        category_labels=json.loads(db_article.category_labels) if db_article.category_labels else [],
        is_breaking=db_article.is_breaking,
        is_published=db_article.is_published,
        pinned_at=db_article.pinned_at,
        priority=db_article.priority,
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
    tags: Optional[str] = Form(""),  # Changed to support comma-separated tags
    category_labels: Optional[str] = Form("[]"),  # New field for category labels
    is_breaking: bool = Form(False),
    is_published: bool = Form(True),
    pin: bool = Form(False),  # Add pin parameter
    priority: int = Form(0),  # Add priority parameter
    featured_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new article with optional image upload"""
    logging.info(f"ARTICLES_FORM inbound title={title!r} category={category} is_breaking={is_breaking} is_published={is_published} pin={pin} priority={priority}")
    
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
    
    # Parse tags - support both comma-separated and JSON format
    try:
        if tags.startswith('[') and tags.endswith(']'):
            tags_list = json.loads(tags) if tags else []
        else:
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
    except:
        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
    
    # Parse category labels
    try:
        category_labels_list = json.loads(category_labels) if category_labels else []
        # Validate category labels against available options
        valid_category_labels = [label for label in category_labels_list if label in AVAILABLE_CATEGORY_LABELS]
    except:
        valid_category_labels = []
    
    # Use robust category coercion
    category_enum = coerce_category(category)
    
    # Sanitize content
    cleaned_content = bleach.clean(
        content, 
        tags=list(bleach.ALLOWED_TAGS) + ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li'],
        strip=True
    )
    
    # Generate UUID and slug for the article
    article_uuid = str(uuid.uuid4())
    article_slug = generate_slug(title, db)
    
    # Handle pinning with timezone-aware datetime
    pinned_at = datetime.now(timezone.utc) if pin else None
    
    # Create database article
    db_article = DBArticle(
        uuid=article_uuid,
        slug=article_slug,
        title=title,
        subheading=subheading,
        content=cleaned_content,
        category=category_enum,
        publisher_name=publisher_name,
        author_name=current_user.username,
        author_id=str(current_user.id),
        featured_image=featured_image_url,
        image_caption=image_caption,
        video_url=video_url,
        tags=json.dumps(tags_list),
        category_labels=json.dumps(valid_category_labels),
        is_breaking=is_breaking,
        is_published=is_published,
        pinned_at=pinned_at,
        priority=priority
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
        category_labels=json.loads(db_article.category_labels) if db_article.category_labels else [],
        is_breaking=db_article.is_breaking,
        is_published=db_article.is_published,
        pinned_at=db_article.pinned_at,
        priority=db_article.priority,
        created_at=db_article.created_at,
        updated_at=db_article.updated_at
    )

@api_router.post("/articles.json", response_model=Article)
async def create_article_json(
    payload: ArticleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create article via JSON (for dashboard without file upload)"""
    logging.info("ARTICLES_JSON inbound")
    
    try:
        # Comprehensive payload logging
        try:
            body = payload.dict()
            logging.info(f"ARTICLES_JSON payload: {json.dumps(body, default=str)[:2000]}")
        except Exception as e:
            logging.warning(f"ARTICLES_JSON could not serialize payload: {e}")
        
        logging.info(f"ARTICLES_JSON user: {current_user.username}, role: {current_user.role}")
        
        # Use robust category coercion
        category_enum = coerce_category(payload.category)
        logging.info(f"ARTICLES_JSON category coerced: '{payload.category}' -> {category_enum}")
        
        # Generate ids/slug
        article_uuid = str(uuid.uuid4())
        article_slug = generate_slug(payload.title, db)
        logging.info(f"ARTICLES_JSON generated: uuid={article_uuid}, slug='{article_slug}'")

        # Filter category labels to only include valid ones
        valid_category_labels = []
        if payload.category_labels:
            valid_category_labels = [label for label in payload.category_labels if label in AVAILABLE_CATEGORY_LABELS]

        # Handle pinning with timezone-aware datetime  
        pinned_at = datetime.now(timezone.utc) if payload.pin else None
        logging.info(f"ARTICLES_JSON pinning: pin={payload.pin}, pinned_at={pinned_at}, priority={payload.priority}")

        logging.info("ARTICLES_JSON creating DBArticle object")
        db_article = DBArticle(
            uuid=article_uuid,
            slug=article_slug,
            title=payload.title,
            subheading=payload.subheading,
            content=payload.content,
            category=category_enum,
            publisher_name=payload.publisher_name or "The Crewkerne Gazette",
            author_name=current_user.username,
            author_id=str(current_user.id),
            featured_image=payload.featured_image,
            image_caption=payload.image_caption,
            video_url=payload.video_url,
            tags=json.dumps(payload.tags or []),
            category_labels=json.dumps(valid_category_labels),
            is_breaking=payload.is_breaking,
            is_published=payload.is_published,
            pinned_at=pinned_at,
            priority=payload.priority,
        )

        logging.info("ARTICLES_JSON adding to database")
        db.add(db_article)
        db.flush()  # Flush to get the ID before commit
        db.commit()
        db.refresh(db_article)
        
        # Simple database verification
        logging.info(f"ARTICLES_JSON: Verifying article {db_article.id} with slug '{db_article.slug}'")
        
        # Basic verification in same session
        verification = db.query(DBArticle).filter(DBArticle.id == db_article.id).first()
        if not verification:
            logging.error(f"ARTICLES_JSON ERROR: Article not found after commit! ID: {db_article.id}")
            raise HTTPException(status_code=500, detail={
                "ok": False,
                "error": "Article creation failed - database verification failed"
            })
        
        logging.info(f"ARTICLES_JSON VERIFIED: Article {db_article.id} successfully saved to database")
        
        logging.info(f"ARTICLES_JSON SUCCESS: Created article id={db_article.id}, slug='{db_article.slug}', category={db_article.category}")

        article_response = Article(
            id=db_article.id,
            uuid=db_article.uuid,
            slug=db_article.slug,
            title=db_article.title,
            subheading=db_article.subheading,
            content=db_article.content,
            category=category_enum,
            publisher_name=db_article.publisher_name,
            author_name=db_article.author_name,
            author_id=db_article.author_id,
            featured_image=db_article.featured_image,
            image_caption=db_article.image_caption,
            video_url=db_article.video_url,
            tags=json.loads(db_article.tags) if db_article.tags else [],
            category_labels=json.loads(db_article.category_labels) if db_article.category_labels else [],
            is_breaking=db_article.is_breaking,
            is_published=db_article.is_published,
            pinned_at=db_article.pinned_at,
            priority=db_article.priority,
            created_at=db_article.created_at,
            updated_at=db_article.updated_at
        )
        
        logging.info(f"ARTICLES_JSON returning successful response for article ID {db_article.id}, slug '{db_article.slug}'")
        return article_response
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        error_msg = f"ARTICLES_JSON failed: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        log_error("create_article_json exception", e)
        raise HTTPException(status_code=500, detail={
            "ok": False,
            "error": "Internal server error while creating article",
            "details": {"message": str(e)}
        })

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
        category_labels=json.loads(db_article.category_labels) if db_article.category_labels else [],
        is_breaking=db_article.is_breaking,
        is_published=db_article.is_published,
        pinned_at=db_article.pinned_at,
        priority=db_article.priority,
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

@api_router.delete("/articles/id/{article_id}")
async def delete_article_by_id(article_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete article by numeric ID"""
    db_article = db.query(DBArticle).filter(DBArticle.id == article_id).first()
    if not db_article:
        raise HTTPException(status_code=404, detail={"error": "Article not found"})
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and db_article.author_id != str(current_user.id):
        raise HTTPException(status_code=403, detail={"error": "You can only delete your own articles"})
    
    article_title = db_article.title
    article_slug = db_article.slug
    db.delete(db_article)
    db.commit()
    
    logger.info(f"🗑️ Article deleted by {current_user.username}: '{article_title}' (ID: {article_id}, slug: {article_slug})")
    
    return {"message": "Article deleted successfully", "deleted_identifier": str(article_id), "title": article_title}

@api_router.delete("/articles/by-slug/{article_slug}")
async def delete_article_by_slug(article_slug: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete article by slug"""
    db_article = db.query(DBArticle).filter(DBArticle.slug == article_slug).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and db_article.author_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only delete your own articles")
    
    article_title = db_article.title
    db.delete(db_article)
    db.commit()
    
    logger.info(f"🗑️ Article deleted by {current_user.username}: '{article_title}' (slug: {article_slug})")
    
    return {"message": "Article deleted successfully", "deleted_article_slug": article_slug, "title": article_title}

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
                    category_labels=json.loads(db_article.category_labels) if db_article.category_labels else [],
                    is_breaking=db_article.is_breaking,
                    is_published=db_article.is_published,
                    pinned_at=db_article.pinned_at,
                    priority=db_article.priority,
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
@api_router.post("/contacts")
async def create_contact(request: Request, db: Session = Depends(get_db)):
    """Create contact message (public endpoint) - simplified for debugging"""
    logger.info('📨 CONTACT: Received POST /api/contacts')
    
    try:
        # Get raw request body for debugging
        body = await request.body()
        logger.info(f"📋 CONTACT: Raw request body: {body}")
        
        # Parse JSON manually to get better error info
        import json
        request_data = json.loads(body)
        logger.info(f"📋 CONTACT: Parsed data: {request_data}")
        
        # Validate required fields
        name = request_data.get('name', '').strip()
        email = request_data.get('email', '').strip()
        message = request_data.get('message', '').strip()
        
        if not name:
            raise HTTPException(status_code=422, detail="Name is required")
        if not email:
            raise HTTPException(status_code=422, detail="Email is required")
        if not message:
            raise HTTPException(status_code=422, detail="Message is required")
        if len(name) > 100:
            raise HTTPException(status_code=422, detail="Name too long (max 100 characters)")
        if len(email) > 100:
            raise HTTPException(status_code=422, detail="Email too long (max 100 characters)")
        if len(message) > 2000:
            raise HTTPException(status_code=422, detail="Message too long (max 2000 characters)")
        
        logger.info(f"📧 CONTACT: Processing - name='{name}', email='{email}', message_length={len(message)}")
        
        # Create database contact
        db_contact = DBContact(
            name=name[:100],  # Ensure length limits
            email=email[:100],
            message=message[:2000]
        )
        
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        
        logger.info(f"✅ CONTACT: Saved to database with ID: {db_contact.id}")
        
        # Return success response
        return {
            "success": True,
            "message": "Contact message saved successfully",
            "contact": {
                "id": db_contact.id,
                "name": db_contact.name,
                "email": db_contact.email,
                "message": db_contact.message,
                "created_at": db_contact.created_at.isoformat()
            }
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ CONTACT: JSON parsing error: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {str(e)}")
    
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
        
    except Exception as e:
        logger.error(f"❌ CONTACT: Database error: {e}")
        logger.error(f"❌ CONTACT: Error type: {type(e).__name__}")
        
        try:
            db.rollback()
        except:
            pass
        
        # Return detailed error for debugging
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {str(e)}"
        )

@api_router.post("/contacts/validate")
async def validate_contact_data(request: Request):
    """Test endpoint to validate contact data format"""
    try:
        body = await request.body()
        import json
        data = json.loads(body)
        
        # Check required fields
        errors = []
        if not data.get('name', '').strip():
            errors.append("Name is required")
        if not data.get('email', '').strip():
            errors.append("Email is required") 
        if not data.get('message', '').strip():
            errors.append("Message is required")
            
        # Check lengths
        name = data.get('name', '')
        email = data.get('email', '')
        message = data.get('message', '')
        
        if len(name) > 100:
            errors.append(f"Name too long: {len(name)}/100")
        if len(email) > 100:
            errors.append(f"Email too long: {len(email)}/100")
        if len(message) > 2000:
            errors.append(f"Message too long: {len(message)}/2000")
            
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "data": {
                "name": name,
                "email": email,
                "message_length": len(message)
            }
        }
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Parsing error: {str(e)}"],
            "data": None
        }

@api_router.post("/contacts/test")
async def test_contact_endpoint(contact_data: ContactCreate):
    """Test contact endpoint without database (for debugging)"""
    logger.info(f"🧪 TEST: Contact received from {contact_data.email}")
    logger.info(f"🧪 TEST: name='{contact_data.name}', email='{contact_data.email}', message_length={len(contact_data.message)}")
    
    return {
        "success": True,
        "message": "Contact test successful - data received correctly",
        "received_data": {
            "name": contact_data.name,
            "email": contact_data.email,
            "message_length": len(contact_data.message)
        }
    }

@api_router.get("/contacts")
async def get_contacts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all contact messages (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logger.info("📋 CONTACTS: Admin requesting contact list")
    
    try:
        db_contacts = db.query(DBContact).order_by(DBContact.created_at.desc()).all()
        logger.info(f"📋 CONTACTS: Found {len(db_contacts)} database contacts")
        
        contacts = []
        for db_contact in db_contacts:
            contacts.append({
                "id": db_contact.id,
                "name": db_contact.name,
                "email": db_contact.email,
                "message": db_contact.message,
                "created_at": db_contact.created_at.isoformat()
            })
        
        logger.info(f"📋 CONTACTS: Returning {len(contacts)} contacts to dashboard")
        return {"contacts": contacts, "total": len(contacts)}
        
    except Exception as db_error:
        logger.error(f"❌ CONTACTS: Database error: {db_error}")
        raise HTTPException(status_code=500, detail=f"Error retrieving contacts: {str(db_error)}")



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



# Health and debug endpoints
@api_router.get("/health")
def health():
    """Health check endpoint"""
    return {"ok": True}

@api_router.get("/whoami")
def whoami(request: Request):
    """Debug endpoint to check origin and auth cookie"""
    return {
        "origin": request.headers.get("origin"),
        "have_auth_cookie": "auth" in request.cookies
    }

@api_router.get("/debug/list-slugs")
async def debug_list_slugs(limit: int = 50, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Debug endpoint to list recent article slugs (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        articles = db.query(DBArticle).order_by(DBArticle.created_at.desc()).limit(limit).all()
        return [
            {
                "id": article.id,
                "slug": article.slug,
                "title": article.title,
                "created_at": article.created_at.isoformat() if article.created_at else None
            }
            for article in articles
        ]
    except Exception as e:
        logger.error(f"Error in debug/list-slugs: {e}")
        return {"error": str(e)}

@api_router.get("/debug/resolve-slug")
async def debug_resolve_slug(slug: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Debug endpoint to resolve and find closest matching slugs"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        original_slug = slug
        normalized_slug = slug.strip().lower()
        
        # Look for exact match (case-insensitive)
        from sqlalchemy import func
        exact_match = db.query(DBArticle).filter(func.lower(DBArticle.slug) == normalized_slug).first()
        
        exact_result = None
        if exact_match:
            exact_result = {
                "id": exact_match.id,
                "slug": exact_match.slug,
                "title": exact_match.title
            }
        
        # Find closest matches using Levenshtein distance
        all_articles = db.query(DBArticle).all()
        closest_matches = []
        
        for article in all_articles:
            distance = calculate_levenshtein_distance(normalized_slug, article.slug.lower())
            closest_matches.append({
                "slug": article.slug,
                "title": article.title,
                "distance": distance
            })
        
        # Sort by distance and take top 5
        closest_matches.sort(key=lambda x: x['distance'])
        closest_matches = closest_matches[:5]
        
        return {
            "input": original_slug,
            "normalized": normalized_slug,
            "exactMatch": exact_result,
            "closest": closest_matches
        }
        
    except Exception as e:
        logger.error(f"Error in debug/resolve-slug: {e}")
        return {"error": str(e)}

@api_router.get("/debug/og")
async def debug_og_values(slug: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Debug endpoint to return exact OG values that crawler page will emit"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Normalize slug for lookup
        normalized_slug = slug.strip().lower()
        
        # Look for article (case-insensitive)
        from sqlalchemy import func
        db_article = db.query(DBArticle).filter(func.lower(DBArticle.slug) == normalized_slug).first()
        
        if db_article:
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
                category_labels=json.loads(db_article.category_labels) if db_article.category_labels else [],
                is_breaking=db_article.is_breaking,
                is_published=db_article.is_published,
                pinned_at=db_article.pinned_at,
                priority=db_article.priority,
                created_at=db_article.created_at,
                updated_at=db_article.updated_at
            )
            
            # Generate OG values as they would appear
            title_safe = article_obj.title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            
            if article_obj.subheading:
                description_safe = article_obj.subheading[:160].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            else:
                import re
                plain_content = re.sub(r'<[^>]+>', '', article_obj.content or '')
                description_safe = plain_content[:160].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            
            image_url = pick_og_image(article_obj)
            image_check = validate_image_url(image_url)
            
            return {
                "ok": True,
                "slug": slug,
                "title": title_safe,
                "description": description_safe,
                "image": image_url,
                "image_check": image_check,
                "url": f"https://crewkernegazette.co.uk/article/{slug}",
                "article_found": True,
                "article_id": article_obj.id
            }
        else:
            # Article not found - return fallback values
            image_url = pick_og_image(None)
            image_check = validate_image_url(image_url)
            
            return {
                "ok": True,
                "slug": slug,
                "title": "Article Not Found | The Crewkerne Gazette",
                "description": "The requested article could not be found on The Crewkerne Gazette.",
                "image": image_url,
                "image_check": image_check,
                "url": f"https://crewkernegazette.co.uk/article/{slug}",
                "article_found": False,
                "article_id": None
            }
            
    except Exception as e:
        logger.error(f"Error in debug/og: {e}")
        
        # Even on error, return safe fallback values
        image_url = pick_og_image(None)
        image_check = validate_image_url(image_url)
        
        return {
            "ok": False,
            "slug": slug,
            "title": "The Crewkerne Gazette",
            "description": "Bold, unapologetic journalism from Somerset to the nation.",
            "image": image_url,
            "image_check": image_check,
            "url": f"https://crewkernegazette.co.uk/article/{slug}",
            "error": str(e),
            "article_found": False
        }

@api_router.get("/debug/env")
async def debug_env(current_user: User = Depends(get_current_user)):
    """Debug endpoint to show masked environment configuration (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Parse DATABASE_URL to get hostname only
        database_host = "unknown"
        database_url = os.getenv('DATABASE_URL', '')
        if database_url:
            import re
            match = re.search(r'@([^:/]+)', database_url)
            if match:
                database_host = match.group(1)
        
        return {
            "cloudinary_cloud_name": os.getenv('CLOUDINARY_CLOUD_NAME', 'not_set'),
            "default_og_image": os.getenv('DEFAULT_OG_IMAGE', 'not_set'),
            "has_cloudinary_key": bool(os.getenv('CLOUDINARY_API_KEY')),
            "has_cloudinary_secret": bool(os.getenv('CLOUDINARY_API_SECRET')),
            "has_fb_app_id": bool(os.getenv('FB_APP_ID')),
            "has_facebook_app_id": bool(os.getenv('FACEBOOK_APP_ID')),
            "database_url_host": database_host,
            "has_jwt_secret": bool(os.getenv('JWT_SECRET')),
            "environment": "development"  # Could be made dynamic
        }
    except Exception as e:
        logger.error(f"Error in debug/env: {e}")
        return {"error": str(e)}

@api_router.get("/debug/check-image")
async def debug_check_image(url: str):
    """Debug endpoint to validate og:image URLs for social media crawlers"""
    try:
        import requests
        
        # Fetch the URL with Facebook crawler user agent
        response = requests.get(
            url, 
            timeout=10, 
            headers={"User-Agent": "facebookexternalhit/1.1"},
            allow_redirects=True
        )
        
        return {
            "url": url,
            "status_code": response.status_code,
            "content_type": response.headers.get('content-type', 'unknown'),
            "content_length": response.headers.get('content-length', 'unknown'),
            "ok": response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'),
            "headers": dict(response.headers),
            "final_url": response.url  # In case of redirects
        }
        
    except Exception as e:
        return {
            "url": url,
            "status_code": 0,
            "content_type": "error",
            "content_length": 0,
            "ok": False,
            "error": str(e),
            "headers": {}
        }

@api_router.get("/debug/article-exists")
async def debug_article_exists(slug: str, db: Session = Depends(get_db)):
    """Debug endpoint to check if article exists by slug"""
    try:
        article = db.query(DBArticle).filter(DBArticle.slug == slug).first()
        return {
            "exists": article is not None,
            "slug": slug,
            "article_id": article.id if article else None,
            "title": article.title if article else None
        }
    except Exception as e:
        return {
            "exists": False,
            "slug": slug,
            "error": str(e)
        }

@api_router.get("/debug/crawler-meta")
async def debug_crawler_meta(slug: str, db: Session = Depends(get_db)):
    """Debug endpoint to preview crawler HTML for an article"""
    try:
        db_article = db.query(DBArticle).filter(DBArticle.slug == slug).first()
        if not db_article:
            return HTMLResponse(
                content=f"""<!DOCTYPE html>
<html><head><title>Debug: Article Not Found</title></head>
<body><h1>Article Not Found</h1><p>No article found with slug: {slug}</p></body>
</html>""",
                status_code=404
            )
        
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
            category_labels=json.loads(db_article.category_labels) if db_article.category_labels else [],
            is_breaking=db_article.is_breaking,
            is_published=db_article.is_published,
            pinned_at=db_article.pinned_at,
            priority=db_article.priority,
            created_at=db_article.created_at,
            updated_at=db_article.updated_at
        )
        
        # Sanitize text content for HTML
        title_safe = article_obj.title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Create safe description - use subheading first, then content excerpt, with proper sanitization
        if article_obj.subheading:
            description_safe = article_obj.subheading[:160].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        else:
            # Strip HTML tags and get plain text excerpt from content
            import re
            plain_content = re.sub(r'<[^>]+>', '', article_obj.content or '')
            description_safe = plain_content[:160].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Safe timestamp handling - use created_at as fallback for updated_at
        updated_iso = (article_obj.updated_at or article_obj.created_at or datetime.now(timezone.utc)).isoformat()
        published_iso = (article_obj.created_at or datetime.now(timezone.utc)).isoformat()
        
        # Ensure og:image uses full absolute URLs
        if article_obj.featured_image and article_obj.featured_image.startswith('http'):
            image_url = article_obj.featured_image
        else:
            image_url = 'https://crewkernegazette.co.uk/logo.png'
        
        debug_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- DEBUG: Preview of crawler meta tags -->
    <title>DEBUG: {title_safe} | The Crewkerne Gazette</title>
    <meta name="description" content="{description_safe}">
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="{title_safe}">
    <meta property="og:description" content="{description_safe}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://crewkernegazette.co.uk/article/{slug}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:site_name" content="The Crewkerne Gazette">
    
    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title_safe}">
    <meta name="twitter:description" content="{description_safe}">
    <meta name="twitter:image" content="{image_url}">
    
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .debug {{ background: #f0f0f0; padding: 15px; margin: 10px 0; border-left: 4px solid #007cba; }}
        .meta-preview {{ background: #fff; border: 1px solid #ddd; padding: 15px; margin: 10px 0; }}
        .image-preview {{ max-width: 200px; height: auto; }}
    </style>
</head>
<body>
    <h1>🔍 DEBUG: Crawler Meta Preview</h1>
    
    <div class="debug">
        <h2>Article Info:</h2>
        <p><strong>Slug:</strong> {slug}</p>
        <p><strong>Title:</strong> {article_obj.title}</p>
        <p><strong>Published:</strong> {published_iso}</p>
        <p><strong>Modified:</strong> {updated_iso}</p>
        <p><strong>Image URL:</strong> {image_url}</p>
    </div>
    
    <div class="meta-preview">
        <h2>Social Media Preview:</h2>
        <img src="{image_url}" alt="Preview Image" class="image-preview" onerror="this.style.display='none'" />
        <h3>{title_safe}</h3>
        <p>{description_safe}</p>
        <small>crewkernegazette.co.uk</small>
    </div>
    
    <div class="debug">
        <h2>Meta Tags Generated:</h2>
        <p>✅ Open Graph title, description, image, type</p>
        <p>✅ Twitter Cards</p>
        <p>✅ JSON-LD structured data</p>
        <p>✅ Canonical URL</p>
    </div>
</body>
</html>"""
        
        return HTMLResponse(content=debug_html, status_code=200)
        
    except Exception as e:
        error_html = f"""<!DOCTYPE html>
<html><head><title>Debug Error</title></head>
<body>
<h1>Debug Error</h1>
<p>Error generating crawler meta for slug: {slug}</p>
<p>Error: {str(e)}</p>
</body>
</html>"""
        return HTMLResponse(content=error_html, status_code=500)

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
@api_router.post("/debug/create-test-article")
async def create_test_article(
    is_breaking: bool = False, 
    pin: bool = False,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Create a test article for mobile debugging (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        # Create test article
        article_data = ArticleCreate(
            title=f"CGZ TEST {timestamp}",
            subheading=f"Test article created at {timestamp}",
            content=f"This is a test article created for debugging purposes on {timestamp}. It includes all standard fields and can be used to verify article creation functionality.",
            category=ArticleCategory.NEWS,
            publisher_name="The Crewkerne Gazette",
            is_breaking=is_breaking,
            is_published=True,
            pin=pin,
            priority=5 if pin else 0,
            tags=["test", "debug", "mobile"],
            category_labels=["News", "Special"] if is_breaking else ["News"]
        )
        
        # Generate unique UUID and slug
        article_uuid = str(uuid.uuid4())
        article_slug = generate_slug(article_data.title, db)
        
        # Create database article
        db_article = DBArticle(
            uuid=article_uuid,
            slug=article_slug,
            title=article_data.title,
            subheading=article_data.subheading,
            content=article_data.content,
            category=article_data.category,
            publisher_name=article_data.publisher_name,
            author_name="Debug System",
            author_id=str(current_user.id),
            featured_image=None,
            image_caption=None,
            video_url=None,
            tags=json.dumps(article_data.tags),
            category_labels=json.dumps(article_data.category_labels),
            is_breaking=article_data.is_breaking,
            is_published=article_data.is_published,
            pinned_at=datetime.now(timezone.utc) if pin else None,
            priority=article_data.priority,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        
        return {
            "ok": True,
            "message": "Test article created successfully",
            "article": {
                "id": db_article.id,
                "uuid": db_article.uuid,
                "slug": db_article.slug,
                "title": db_article.title,
                "is_breaking": db_article.is_breaking,
                "pinned_at": db_article.pinned_at,
                "priority": db_article.priority,
                "url": f"/article/{db_article.slug}"
            }
        }
        
    except Exception as e:
        error_msg = f"Failed to create test article: {str(e)}"
        log_error(error_msg, e)
        raise HTTPException(status_code=500, detail={
            "ok": False,
            "error": "Test article creation failed",
            "details": {"message": str(e)}
        })

@api_router.get("/debug/last-errors")
async def get_last_errors():
    """Get last 20 error logs for mobile debugging (no auth required)"""
    try:
        return {
            "ok": True,
            "errors": list(ERROR_LOG_BUFFER),
            "count": len(ERROR_LOG_BUFFER),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"Failed to retrieve error logs: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@api_router.get("/debug/database-info")
async def debug_database_info():
    """Check database connection and column information"""
    try:
        from sqlalchemy import create_engine, text
        import os
        
        DATABASE_URL = os.getenv('DATABASE_URL', 'Not set')
        
        # Mask password for security
        display_url = DATABASE_URL
        if '@' in display_url:
            parts = display_url.split('@')
            if len(parts) > 1:
                user_part = parts[0].split('://')[-1]
                if ':' in user_part:
                    user, _ = user_part.split(':', 1)
                    display_url = display_url.replace(user_part, f"{user}:***")
        
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Get table info
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'articles'
                ORDER BY column_name;
            """))
            
            columns = [row[0] for row in result.fetchall()]
            
            # Check for our specific columns
            new_columns = ['category_labels', 'pinned_at', 'priority']
            has_columns = {col: col in columns for col in new_columns}
            
            return {
                "ok": True,
                "database_url": display_url,
                "articles_table_columns": columns,
                "required_columns_status": has_columns,
                "all_required_present": all(has_columns.values())
            }
            
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "database_url": display_url if 'display_url' in locals() else "Unknown"
        }

@api_router.get("/debug/create-test-article-simple")
async def create_test_article_simple(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a simple test article for mobile smoke testing (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin required")
    
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        title = f"CGZ TEST {timestamp}"
        article_uuid = str(uuid.uuid4())
        slug = generate_slug(title, db)
        
        db_article = DBArticle(
            uuid=article_uuid,
            slug=slug,
            title=title,
            subheading="Smoke test (pinned & breaking)",
            content="Automated test content for production validation.",
            category=ArticleCategory.NEWS,
            publisher_name="The Crewkerne Gazette",
            author_name=current_user.username,
            author_id=str(current_user.id),
            tags=json.dumps(["test", "smoke"]),
            category_labels=json.dumps(["News", "Special"]),
            is_breaking=True,
            is_published=True,
            priority=10,
            pinned_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        
        return {
            "ok": True, 
            "slug": slug,
            "title": title,
            "url": f"/article/{slug}",
            "is_breaking": True,
            "pinned_at": db_article.pinned_at,
            "priority": db_article.priority
        }
        
    except Exception as e:
        error_msg = f"Failed to create simple test article: {str(e)}"
        log_error(error_msg, e)
        raise HTTPException(status_code=500, detail={
            "ok": False,
            "error": "Test article creation failed",
            "details": {"message": str(e)}
        })

@api_router.get("/debug/deployment-test")
async def debug_deployment_test():
    """Test if the latest backend changes are deployed"""
    import datetime
    return {
        "ok": True,
        "message": "Backend deployment test endpoint - latest changes active",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "post-duplicate-code-fix"
    }

@api_router.get("/debug/article-exists")
async def debug_article_exists(slug: str, db: Session = Depends(get_db)):
    """Check if an article with the given slug exists"""
    try:
        article = db.query(DBArticle).filter(DBArticle.slug == slug).first()
        return {
            "exists": bool(article),
            "slug": slug,
            "article_id": article.id if article else None,
            "article_title": article.title if article else None
        }
    except Exception as e:
        return {"exists": False, "error": str(e)}

@api_router.post("/debug/seed-one", tags=["debug"])
async def debug_seed_one(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a single seed article to prove DB writes work in production (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin required")
    
    try:
        now = datetime.now(timezone.utc)
        title = f"SEED {now.strftime('%Y%m%d_%H%M%S')}"
        slug = generate_slug(title, db)
        
        db_article = DBArticle(
            uuid=str(uuid.uuid4()),
            slug=slug,
            title=title,
            subheading="seed",
            content="seed content",
            category=ArticleCategory.NEWS,
            publisher_name="The Crewkerne Gazette",
            author_name=current_user.username,
            author_id=str(current_user.id),
            is_breaking=True,
            is_published=True,
            pinned_at=now,
            priority=10,
            tags=json.dumps(["seed"]),
            category_labels=json.dumps(["News", "Special"]),
            created_at=now,
            updated_at=now,
        )
        
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        
        logging.info(f"DEBUG_SEED_ONE: Successfully created article id={db_article.id}, slug='{db_article.slug}'")
        
        return {"ok": True, "slug": db_article.slug}
        
    except Exception as e:
        error_msg = f"Failed to seed article: {str(e)}"
        logging.error(f"DEBUG_SEED_ONE failed: {error_msg}\n{traceback.format_exc()}")
        log_error(error_msg, e)
        raise HTTPException(status_code=500, detail={
            "ok": False,
            "error": "Seed article creation failed",
            "details": {"message": str(e)}
        })

@api_router.get("/articles/{article_slug}/structured-data")
async def get_article_structured_data(article_slug: str, db: Session = Depends(get_db)):
    """Generate structured data for an article"""
    db_article = db.query(DBArticle).filter(DBArticle.slug == article_slug).first()
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
            "@id": f"https://crewkernegazette.co.uk/article/{article_slug}"
        },
        "articleSection": db_article.category.value,
        "keywords": ", ".join(json.loads(db_article.tags)) if db_article.tags else db_article.category.value
    }

# SEO Routes
@app.get("/sitemap.xml")
async def generate_sitemap(db: Session = Depends(get_db)):
    """Generate dynamic sitemap for SEO"""
    try:
        published_articles = db.query(DBArticle).filter(DBArticle.is_published == True).order_by(DBArticle.updated_at.desc()).all()
        
        # Start sitemap XML
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://crewkernegazette.co.uk/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://crewkernegazette.co.uk/news</loc>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://crewkernegazette.co.uk/music</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://crewkernegazette.co.uk/documentaries</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://crewkernegazette.co.uk/comedy</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://crewkernegazette.co.uk/contact</loc>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>"""
        
        # Add articles
        for article in published_articles:
            last_modified = article.updated_at.strftime('%Y-%m-%d')
            sitemap_xml += f"""
    <url>
        <loc>https://crewkernegazette.co.uk/article/{article.slug}</loc>
        <lastmod>{last_modified}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>"""
        
        sitemap_xml += "\n</urlset>"
        
        return HTMLResponse(content=sitemap_xml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Sitemap generation error: {e}")
        # Return basic sitemap on error
        basic_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://crewkernegazette.co.uk/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>"""
        return HTMLResponse(content=basic_sitemap, media_type="application/xml")

@app.get("/news-sitemap.xml") 
async def generate_news_sitemap(db: Session = Depends(get_db)):
    """Generate Google News sitemap"""
    try:
        # Get recent published articles (last 7 days for news)
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        
        recent_articles = db.query(DBArticle).filter(
            DBArticle.is_published == True,
            DBArticle.created_at >= week_ago
        ).order_by(DBArticle.created_at.desc()).limit(1000).all()
        
        # Start news sitemap XML
        news_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">"""
        
        # Add articles
        for article in recent_articles:
            publication_date = article.created_at.strftime('%Y-%m-%d')
            title_escaped = article.title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            
            news_sitemap += f"""
    <url>
        <loc>https://crewkernegazette.co.uk/article/{article.slug}</loc>
        <news:news>
            <news:publication>
                <news:name>The Crewkerne Gazette</news:name>
                <news:language>en</news:language>
            </news:publication>
            <news:publication_date>{publication_date}</news:publication_date>
            <news:title>{title_escaped}</news:title>
        </news:news>
    </url>"""
        
        news_sitemap += "\n</urlset>"
        
        return HTMLResponse(content=news_sitemap, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"News sitemap generation error: {e}")
        # Return empty news sitemap on error
        empty_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
</urlset>"""
        return HTMLResponse(content=empty_sitemap, media_type="application/xml")

@app.get("/robots.txt")
async def robots_txt():
    """Generate robots.txt for search engines"""
    robots_content = """User-agent: *
Allow: /

# Sitemaps
Sitemap: https://crewkernegazette.co.uk/sitemap.xml
Sitemap: https://crewkernegazette.co.uk/news-sitemap.xml

# Admin areas
Disallow: /dashboard
Disallow: /login
Disallow: /api/

# Allow article pages
Allow: /article/

# Crawl delay
Crawl-delay: 1
"""
    return HTMLResponse(content=robots_content, media_type="text/plain")

# Include router and middleware
app.include_router(api_router)

# Mount frontend static files FIRST for static assets
# Mount static files (only if directory exists)
static_dir = Path("../frontend/build/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="../frontend/build/static"), name="static")
else:
    logger.warning("Static files directory not found, skipping mount")

# SPA fallback route - catch all non-API routes and serve React app
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "HEAD"], include_in_schema=False)
async def spa_fallback(path: str, request: Request):
    """Serve React app for all non-API routes (SPA routing support)"""
    if not path.startswith('api/') and not path.startswith('static/') and not path.startswith('article/') and not path.startswith('og/'):
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

ALLOWED_ORIGINS = [
    "https://crewkernegazette.co.uk",  # production frontend
    "https://www.crewkernegazette.co.uk",  # www subdomain
    "http://localhost:5173",           # Vite dev (if applicable)
    "http://localhost:3000",           # CRA/Next dev (if applicable)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
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