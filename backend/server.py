from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app
app = FastAPI(title="Crewkerne Gazette API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'emergency-fallback-secret-key')
JWT_ALGORITHM = 'HS256'

security = HTTPBearer()

# Emergency storage - replaces database
emergency_articles = []
emergency_contacts = []
emergency_settings = {
    "maintenance_mode": False,
    "show_breaking_news_banner": True
}
emergency_users = {
    "admin": {
        "id": "admin-id",
        "username": "admin", 
        "email": "admin@crewkernegazette.com",
        "role": "admin",
        "password_hash": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
    },
    "Gazette": {
        "id": "gazette-id", 
        "username": "Gazette",
        "email": "gazette@crewkernegazette.com", 
        "role": "admin",
        "password_hash": bcrypt.hashpw("80085".encode(), bcrypt.gensalt()).decode()
    }
}

# Enums
class ArticleCategory(str, Enum):
    NEWS = "news"
    MUSIC = "music"
    DOCUMENTARIES = "documentaries"
    COMEDY = "comedy"

class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"

class ContactStatus(str, Enum):
    NEW = "new"
    READ = "read"
    REPLIED = "replied"

# Models with validation
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    role: UserRole = UserRole.EDITOR
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserLogin(BaseModel):
    username: str
    password: str

class Article(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=1, max_length=200)
    subheading: Optional[str] = Field(None, max_length=300)
    content: str = Field(..., min_length=1)
    category: ArticleCategory
    author_id: str
    author_name: str = ""
    publisher_name: str = "The Crewkerne Gazette"
    featured_image: Optional[str] = Field(None)
    image_caption: Optional[str] = Field(None, max_length=200)
    video_url: Optional[str] = Field(None)
    is_breaking: bool = False
    is_published: bool = True
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('content', 'title', 'subheading')
    def sanitize_html(cls, v):
        if v:
            return bleach.clean(v, tags=['p', 'br', 'strong', 'em', 'u', 'a'], attributes={'a': ['href']})
        return v
    
    @validator('featured_image')
    def validate_image(cls, v):
        if v and v.startswith('data:image/'):
            # Check base64 size limit (5MB)
            try:
                header, data = v.split(',', 1)
                decoded_size = len(base64.b64decode(data))
                if decoded_size > 5 * 1024 * 1024:  # 5MB limit
                    raise ValueError("Image too large (max 5MB)")
            except:
                raise ValueError("Invalid base64 image")
        return v

class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    subheading: Optional[str] = Field(None, max_length=300)
    content: str = Field(..., min_length=1)
    category: ArticleCategory
    publisher_name: Optional[str] = "The Crewkerne Gazette"
    featured_image: Optional[str] = Field(None)
    image_caption: Optional[str] = Field(None, max_length=200)
    video_url: Optional[str] = Field(None)
    is_breaking: bool = False
    is_published: bool = True
    tags: List[str] = []

class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    inquiry: str = Field(..., min_length=1, max_length=1000)
    status: ContactStatus = ContactStatus.NEW
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactCreate(BaseModel):
    email: EmailStr
    inquiry: str = Field(..., min_length=1, max_length=1000)

class MaintenanceToggle(BaseModel):
    maintenance_mode: bool

class BreakingNewsBanner(BaseModel):
    show_breaking_news_banner: bool

# Utility Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_jwt_token(user_id: str, username: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        username = payload.get('username')
        role = payload.get('role')
        
        if user_id is None or username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return User(
            id=user_id,
            username=username,
            email=f"{username}@crewkernegazette.com",
            role=role,
            created_at=datetime.now(timezone.utc)
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes
@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    if user_data.username in emergency_users:
        user = emergency_users[user_data.username]
        if verify_password(user_data.password, user['password_hash']):
            token = create_jwt_token(user['id'], user['username'], user['role'])
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": User(**user)
            }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@api_router.post("/contact", response_model=Contact)
async def submit_contact(contact_data: ContactCreate):
    contact_obj = Contact(**contact_data.dict())
    emergency_contacts.append(contact_obj.dict())
    return contact_obj

@api_router.post("/articles", response_model=Article)
async def create_article(article_data: ArticleCreate, current_user: User = Depends(get_current_user)):
    print(f"📰 Creating article: {article_data.title}")
    if article_data.featured_image:
        print(f"🖼️  Article has image - Length: {len(article_data.featured_image)} chars")
    
    article_dict = article_data.dict()
    article_dict['author_id'] = current_user.id
    article_dict['author_name'] = current_user.username
    article_dict['updated_at'] = datetime.now(timezone.utc)
    article_obj = Article(**article_dict)
    emergency_articles.append(article_obj.dict())
    
    print(f"✅ Article stored - Total articles: {len(emergency_articles)}")
    return article_obj

@api_router.get("/articles", response_model=List[Article])
async def get_articles(category: Optional[str] = None, is_breaking: Optional[bool] = None, limit: int = 20):
    articles = emergency_articles.copy()
    if category:
        articles = [a for a in articles if a.get("category") == category]
    if is_breaking is not None:
        articles = [a for a in articles if a.get("is_breaking") == is_breaking]
    
    # Improved sorting with fallback
    articles = sorted(articles, key=lambda x: x.get("created_at", datetime.min.isoformat()), reverse=True)[:limit]
    return [Article(**article) for article in articles]

@api_router.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: str):
    """Get individual article by ID with structured data"""
    for article in emergency_articles:
        if article.get("id") == article_id:
            return Article(**article)
    raise HTTPException(status_code=404, detail="Article not found")

@api_router.get("/articles/{article_id}/related")
async def get_related_articles(article_id: str):
    """Get related articles"""
    current_article = None
    for article in emergency_articles:
        if article.get("id") == article_id:
            current_article = article
            break
    
    if not current_article:
        return []
    
    # Get other articles in same category
    related = []
    for article in emergency_articles:
        if (article.get("id") != article_id and 
            article.get("category") == current_article.get("category") and
            len(related) < 3):
            related.append(Article(**article))
    
    return related

@api_router.get("/articles/{article_id}/structured-data")
async def get_article_structured_data(article_id: str):
    """Generate structured data for an article"""
    for article in emergency_articles:
        if article.get("id") == article_id:
            article_obj = Article(**article)
            return {
                "@context": "https://schema.org",
                "@type": "NewsArticle",
                "headline": article_obj.title,
                "description": article_obj.subheading or article_obj.content[:160],
                "image": article_obj.featured_image or "https://crewkernegazette.co.uk/logo.png",
                "datePublished": article_obj.created_at.isoformat(),
                "dateModified": article_obj.updated_at.isoformat(),
                "author": {
                    "@type": "Person",
                    "name": article_obj.author_name or article_obj.publisher_name
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
                    "@id": f"https://crewkernegazette.co.uk/article/{article_id}"
                },
                "articleSection": article_obj.category,
                "keywords": ", ".join(article_obj.tags) if article_obj.tags else article_obj.category
            }
    raise HTTPException(status_code=404, detail="Article not found")

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Emergency dashboard stats"""
    query_articles = emergency_articles.copy()
    if current_user.role != UserRole.ADMIN:
        query_articles = [a for a in query_articles if a.get("author_id") == current_user.id]
    
    return {
        "total_articles": len(query_articles),
        "published_articles": len([a for a in query_articles if a.get("is_published", True)]),
        "breaking_news": len([a for a in query_articles if a.get("is_breaking", False)]),
        "total_contacts": len(emergency_contacts),
        "new_contacts": len([c for c in emergency_contacts if c.get("status") == "new"]),
        "categories": {
            "news": len([a for a in query_articles if a.get("category") == "news"]),
            "music": len([a for a in query_articles if a.get("category") == "music"]),
            "documentaries": len([a for a in query_articles if a.get("category") == "documentaries"]),
            "comedy": len([a for a in query_articles if a.get("category") == "comedy"])
        },
        "emergency_mode": True
    }

@api_router.get("/dashboard/articles", response_model=List[Article])
async def get_dashboard_articles(current_user: User = Depends(get_current_user)):
    articles = emergency_articles.copy()
    if current_user.role != UserRole.ADMIN:
        articles = [a for a in articles if a.get("author_id") == current_user.id]
    articles = sorted(articles, key=lambda x: x.get("created_at", datetime.min.isoformat()), reverse=True)
    return [Article(**article) for article in articles]

@api_router.put("/articles/{article_id}", response_model=Article)
async def update_article(article_id: str, article_data: ArticleCreate, current_user: User = Depends(get_current_user)):
    """Update an existing article"""
    # Find the article to update
    article_index = None
    for i, article in enumerate(emergency_articles):
        if article.get("id") == article_id:
            article_index = i
            break
    
    if article_index is None:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check permissions
    existing_article = emergency_articles[article_index]
    if current_user.role != UserRole.ADMIN and existing_article.get("author_id") != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own articles")
    
    # Update the article
    updated_article = {
        **existing_article,  # Keep existing fields
        "title": article_data.title,
        "subheading": article_data.subheading,
        "content": article_data.content,
        "category": article_data.category,
        "publisher_name": article_data.publisher_name or "The Crewkerne Gazette",
        "featured_image": article_data.featured_image,
        "image_caption": article_data.image_caption,
        "video_url": article_data.video_url,
        "is_breaking": article_data.is_breaking,
        "is_published": article_data.is_published,
        "tags": article_data.tags,
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Replace the article in emergency storage
    emergency_articles[article_index] = updated_article
    
    return Article(**updated_article)

@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str, current_user: User = Depends(get_current_user)):
    """Delete an article"""
    # Find the article to delete
    article_index = None
    for i, article in enumerate(emergency_articles):
        if article.get("id") == article_id:
            article_index = i
            break
    
    if article_index is None:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check permissions
    existing_article = emergency_articles[article_index]
    if current_user.role != UserRole.ADMIN and existing_article.get("author_id") != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own articles")
    
    # Remove the article from emergency storage
    deleted_article = emergency_articles.pop(article_index)
    
    return {"message": "Article deleted successfully", "deleted_article_id": article_id}

@api_router.get("/contacts", response_model=List[Contact])
async def get_contacts(current_user: User = Depends(get_current_user)):
    return [Contact(**contact) for contact in emergency_contacts]

@api_router.get("/settings/public")
async def get_public_settings():
    return {"show_breaking_news_banner": emergency_settings.get("show_breaking_news_banner", True)}

@api_router.get("/settings")
async def get_settings(current_user: User = Depends(get_current_user)):
    """Get admin settings"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return emergency_settings

@api_router.post("/settings/maintenance")
async def toggle_maintenance(maintenance_data: MaintenanceToggle, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    emergency_settings["maintenance_mode"] = maintenance_data.maintenance_mode
    return {"message": f"Maintenance mode {'enabled' if maintenance_data.maintenance_mode else 'disabled'}"}

@api_router.post("/settings/breaking-news-banner")
async def toggle_breaking_news_banner(banner_data: BreakingNewsBanner, current_user: User = Depends(get_current_user)):
    """Toggle breaking news banner"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    emergency_settings["show_breaking_news_banner"] = banner_data.show_breaking_news_banner
    status_text = "enabled" if banner_data.show_breaking_news_banner else "disabled"
    return {"message": f"Breaking news banner {status_text} successfully"}

@api_router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    print(f"🔍 Upload started - File: {file.filename}, Type: {file.content_type}, Size: {file.size}")
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Size limit check (5MB)
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
    
    # Read file content
    file_content = await file.read()
    print(f"📁 File content read - Size: {len(file_content)} bytes")
    
    # Convert to base64
    base64_string = base64.b64encode(file_content).decode('utf-8')
    print(f"📝 Base64 created - Length: {len(base64_string)} characters")
    
    # Create data URI for immediate use
    mime_type = file.content_type
    data_uri = f"data:{mime_type};base64,{base64_string}"
    print(f"🌐 Data URI created - Total length: {len(data_uri)} characters")
    
    return {"url": data_uri, "debug": {"size": len(file_content), "base64_length": len(base64_string)}}

# Debug endpoints
@api_router.get("/debug/articles")
async def debug_articles():
    """Debug endpoint to see all articles in memory"""
    return {
        "total_articles": len(emergency_articles),
        "articles": emergency_articles,
        "sample_article_ids": [a.get("id") for a in emergency_articles[:5]]
    }

@api_router.get("/debug/settings")
async def debug_settings():
    """Debug endpoint to see current settings"""
    return {
        "current_settings": emergency_settings
    }

# Add some sample articles
emergency_articles.extend([
    {
        "id": str(uuid.uuid4()),
        "title": "Welcome to The Crewkerne Gazette",
        "subheading": "Your trusted source for local news and investigations",
        "content": "The Crewkerne Gazette is now running with full functionality. All features work seamlessly including article creation, image uploads, social sharing, and breaking news management.",
        "category": "news",
        "author_id": "admin-id", 
        "author_name": "admin",
        "publisher_name": "The Crewkerne Gazette",
        "is_breaking": True,
        "is_published": True,
        "tags": ["welcome", "announcement", "local"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
])

# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("✅ Crewkerne Gazette API ready - All functions work without database!")