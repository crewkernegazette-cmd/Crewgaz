from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from enum import Enum
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Create the main app without a prefix
app = FastAPI()

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

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

# Models
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
    title: str
    subheading: Optional[str] = None
    content: str
    category: ArticleCategory
    author_id: str
    author_name: str = ""
    publisher_name: str = "The Crewkerne Gazette"
    featured_image: Optional[str] = None
    image_caption: Optional[str] = None
    video_url: Optional[str] = None
    is_breaking: bool = False
    is_published: bool = True
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ArticleCreate(BaseModel):
    title: str
    subheading: Optional[str] = None
    content: str
    category: ArticleCategory
    publisher_name: Optional[str] = "The Crewkerne Gazette"
    featured_image: Optional[str] = None
    image_caption: Optional[str] = None
    video_url: Optional[str] = None
    is_breaking: bool = False
    is_published: bool = True
    tags: List[str] = []

class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    inquiry: str
    status: ContactStatus = ContactStatus.NEW
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactCreate(BaseModel):
    email: EmailStr
    inquiry: str

class MaintenanceToggle(BaseModel):
    maintenance_mode: bool

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
    article_dict = article_data.dict()
    article_dict['author_id'] = current_user.id
    article_dict['author_name'] = current_user.username
    article_obj = Article(**article_dict)
    emergency_articles.append(article_obj.dict())
    return article_obj

@api_router.get("/articles", response_model=List[Article])
async def get_articles(category: Optional[str] = None, is_breaking: Optional[bool] = None, limit: int = 20):
    articles = emergency_articles.copy()
    if category:
        articles = [a for a in articles if a.get("category") == category]
    if is_breaking is not None:
        articles = [a for a in articles if a.get("is_breaking") == is_breaking]
    articles = sorted(articles, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]
    return [Article(**article) for article in articles]

@api_router.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: str):
    """Get individual article by ID"""
    for article in emergency_articles:
        if article.get("id") == article_id:
            return Article(**article)
    raise HTTPException(status_code=404, detail="Article not found")

@api_router.get("/articles/{article_id}/related")
async def get_related_articles(article_id: str):
    """Get related articles"""
    # Find current article
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

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
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
    articles = sorted(articles, key=lambda x: x.get("created_at", ""), reverse=True)
    return [Article(**article) for article in articles]

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
async def toggle_breaking_news_banner(banner_data: dict, current_user: User = Depends(get_current_user)):
    """Toggle breaking news banner"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    emergency_settings["show_breaking_news_banner"] = banner_data.get("show_breaking_news_banner", True)
    status_text = "enabled" if banner_data.get("show_breaking_news_banner") else "disabled"
    return {"message": f"Breaking news banner {status_text} successfully"}

@api_router.post("/settings/maintenance")
async def toggle_maintenance(maintenance_data: MaintenanceToggle, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    emergency_settings["maintenance_mode"] = maintenance_data.maintenance_mode
    return {"message": f"Maintenance mode {'enabled' if maintenance_data.maintenance_mode else 'disabled'}"}

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

@api_router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    print(f"🔍 Upload started - File: {file.filename}, Type: {file.content_type}, Size: {file.size}")
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read file content
    file_content = await file.read()
    print(f"📁 File content read - Size: {len(file_content)} bytes")
    
    # Convert to base64
    import base64
    base64_string = base64.b64encode(file_content).decode('utf-8')
    print(f"📝 Base64 created - Length: {len(base64_string)} characters")
    print(f"🔤 Base64 start: {base64_string[:100]}...")
    
    # Create data URI for immediate use
    mime_type = file.content_type
    data_uri = f"data:{mime_type};base64,{base64_string}"
    print(f"🌐 Data URI created - Total length: {len(data_uri)} characters")
    
    return {"url": data_uri, "debug": {"size": len(file_content), "base64_length": len(base64_string)}}

# Remove the old uploads serving endpoint since we don't need it

@api_router.get("/uploads-test/{filename}")
async def test_upload_serving(filename: str):
    """Test endpoint to check if uploaded files are accessible"""
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        return {"status": "file exists", "path": str(file_path), "size": file_path.stat().st_size}
    else:
        return {"status": "file not found", "path": str(file_path)}

# Add some sample articles
emergency_articles.extend([
    {
        "id": str(uuid.uuid4()),
        "title": "Welcome to Emergency Mode",
        "content": "The Crewkerne Gazette is now running in emergency mode. All functions work without database.",
        "category": "news",
        "author_id": "admin-id", 
        "author_name": "admin",
        "publisher_name": "The Crewkerne Gazette",
        "is_breaking": True,
        "is_published": True,
        "tags": [],
        "created_at": datetime.now(timezone.utc)
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

print("Emergency backend created - all functions work without database!")
