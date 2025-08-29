from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
# Add connection options for better Atlas compatibility
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=5000,
    maxPoolSize=10,
    retryWrites=True
)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# JWT Configuration
JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = 'HS256'

security = HTTPBearer()

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

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole = UserRole.EDITOR

class UserLogin(BaseModel):
    username: str
    password: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

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

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    subheading: Optional[str] = None
    content: Optional[str] = None
    category: Optional[ArticleCategory] = None
    publisher_name: Optional[str] = None
    featured_image: Optional[str] = None
    image_caption: Optional[str] = None
    video_url: Optional[str] = None
    is_breaking: Optional[bool] = None
    is_published: Optional[bool] = None
    tags: Optional[List[str]] = None

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

class ContactUpdate(BaseModel):
    status: Optional[ContactStatus] = None

class SiteSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    maintenance_mode: bool = False
    show_breaking_news_banner: bool = True
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MaintenanceToggle(BaseModel):
    maintenance_mode: bool

class BreakingNewsBannerToggle(BaseModel):
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
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
            
        return User(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def check_maintenance_mode():
    settings = await db.settings.find_one()
    if settings and settings.get('maintenance_mode', False):
        return True
    return False

# Maintenance mode middleware
@app.middleware("http")
async def maintenance_middleware(request: Request, call_next):
    # Skip maintenance check for admin routes and API
    if request.url.path.startswith("/api") or request.url.path.startswith("/uploads") or "login" in request.url.path or "dashboard" in request.url.path:
        response = await call_next(request)
        return response
    
    # Check if maintenance mode is enabled
    if await check_maintenance_mode():
        maintenance_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Under Maintenance - The Crewkerne Gazette</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: 'Arial', sans-serif;
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    color: #f1f5f9;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    text-align: center;
                }
                .container {
                    max-width: 600px;
                    padding: 2rem;
                }
                .logo {
                    width: 100px;
                    height: 100px;
                    margin: 0 auto 2rem;
                    background: #B91C1C;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border: 3px solid #f1f5f9;
                    position: relative;
                }
                .logo::before {
                    content: '';
                    position: absolute;
                    top: 15%;
                    left: 15%;
                    right: 15%;
                    height: 30%;
                    background: #f1f5f9;
                    border-radius: 50px 50px 0 0;
                }
                .logo::after {
                    content: '';
                    position: absolute;
                    bottom: 15%;
                    left: 15%;
                    right: 15%;
                    height: 30%;
                    background: #f1f5f9;
                    border-radius: 0 0 50px 50px;
                }
                h1 {
                    font-size: 2.5rem;
                    margin-bottom: 1rem;
                    color: #B91C1C;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                }
                p {
                    font-size: 1.2rem;
                    margin-bottom: 2rem;
                    color: #cbd5e1;
                }
                .maintenance-image {
                    width: 300px;
                    height: 200px;
                    margin: 2rem auto;
                    background: url('https://images.unsplash.com/photo-1581833971358-2c8b550f87b3') center/cover;
                    border-radius: 12px;
                    border: 2px solid #B91C1C;
                }
                .tagline {
                    font-style: italic;
                    color: #94a3b8;
                    margin-top: 2rem;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo"></div>
                <h1>Under Maintenance</h1>
                <p>The Crewkerne Gazette is currently undergoing some improvements.<br>
                   We'll be back shortly with even better content!</p>
                <div class="maintenance-image"></div>
                <p class="tagline">"Where common sense meets headlines"</p>
                <p><strong>Please stand by...</strong></p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=maintenance_html, status_code=503)
    
    response = await call_next(request)
    return response

# File Upload Route
@api_router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return the URL path
    file_url = f"/uploads/{unique_filename}"
    return {"url": file_url}

# Auth Routes
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user_dict = user_data.dict()
    user_dict.pop('password')
    user_obj = User(**user_dict)
    
    # Store user with hashed password
    user_doc = user_obj.dict()
    user_doc['password_hash'] = hashed_password
    
    await db.users.insert_one(user_doc)
    return user_obj

@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    # Find user
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = create_jwt_token(user['id'], user['username'], user['role'])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": User(**user)
    }

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.post("/auth/change-password")
async def change_password(password_data: PasswordChange, current_user: User = Depends(get_current_user)):
    # Get current user from database
    user = await db.users.find_one({"id": current_user.id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(password_data.current_password, user['password_hash']):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Hash new password
    new_password_hash = hash_password(password_data.new_password)
    
    # Update password
    await db.users.update_one(
        {"id": current_user.id}, 
        {"$set": {"password_hash": new_password_hash}}
    )
    
    return {"message": "Password changed successfully"}

# Settings Routes
@api_router.get("/settings")
async def get_settings(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = await db.settings.find_one()
    if not settings:
        # Create default settings
        default_settings = SiteSettings()
        await db.settings.insert_one(default_settings.dict())
        return default_settings
    
    return SiteSettings(**settings)

@api_router.get("/settings/public")
async def get_public_settings():
    """Get public settings that don't require authentication"""
    settings = await db.settings.find_one()
    if not settings:
        return {"show_breaking_news_banner": True}
    
    return {
        "show_breaking_news_banner": settings.get("show_breaking_news_banner", True)
    }

@api_router.post("/settings/maintenance")
async def toggle_maintenance(maintenance_data: MaintenanceToggle, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Update or create settings
    update_data = {
        "maintenance_mode": maintenance_data.maintenance_mode,
        "updated_at": datetime.now(timezone.utc)
    }
    
    result = await db.settings.update_one(
        {},
        {"$set": update_data},
        upsert=True
    )
    
    status_text = "enabled" if maintenance_data.maintenance_mode else "disabled"
    return {"message": f"Maintenance mode {status_text} successfully"}

@api_router.post("/settings/breaking-news-banner")
async def toggle_breaking_news_banner(banner_data: BreakingNewsBannerToggle, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Update or create settings
    update_data = {
        "show_breaking_news_banner": banner_data.show_breaking_news_banner,
        "updated_at": datetime.now(timezone.utc)
    }
    
    result = await db.settings.update_one(
        {},
        {"$set": update_data},
        upsert=True
    )
    
    status_text = "enabled" if banner_data.show_breaking_news_banner else "disabled"
    return {"message": f"Breaking news banner {status_text} successfully"}

# Article Routes
@api_router.post("/articles", response_model=Article)
async def create_article(article_data: ArticleCreate, current_user: User = Depends(get_current_user)):
    article_dict = article_data.dict()
    article_dict['author_id'] = current_user.id
    article_dict['author_name'] = current_user.username
    article_obj = Article(**article_dict)
    
    await db.articles.insert_one(article_obj.dict())
    return article_obj

@api_router.get("/articles", response_model=List[Article])
async def get_articles(category: Optional[str] = None, is_breaking: Optional[bool] = None, limit: int = 20):
    query = {"is_published": True}
    if category:
        query["category"] = category
    if is_breaking is not None:
        query["is_breaking"] = is_breaking
    
    articles = await db.articles.find(query).sort("created_at", -1).limit(limit).to_list(length=None)
    return [Article(**article) for article in articles]

@api_router.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: str):
    article = await db.articles.find_one({"id": article_id, "is_published": True})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return Article(**article)

@api_router.get("/articles/{article_id}/related")
async def get_related_articles(article_id: str):
    # Get current article to exclude it and get same category
    current_article = await db.articles.find_one({"id": article_id})
    if not current_article:
        return []
    
    # Get other latest articles, prioritizing same category
    related_articles = await db.articles.find({
        "id": {"$ne": article_id},
        "is_published": True,
        "category": current_article.get("category")
    }).sort("created_at", -1).limit(3).to_list(length=None)
    
    # If not enough same category, fill with other articles
    if len(related_articles) < 3:
        additional_articles = await db.articles.find({
            "id": {"$ne": article_id},
            "is_published": True,
            "category": {"$ne": current_article.get("category")}
        }).sort("created_at", -1).limit(3 - len(related_articles)).to_list(length=None)
        related_articles.extend(additional_articles)
    
    return [Article(**article) for article in related_articles]

@api_router.put("/articles/{article_id}", response_model=Article)
async def update_article(article_id: str, article_data: ArticleUpdate, current_user: User = Depends(get_current_user)):
    # Check if article exists and user owns it or is admin
    article = await db.articles.find_one({"id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if article['author_id'] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to update this article")
    
    # Update article
    update_data = {k: v for k, v in article_data.dict().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc)
    
    await db.articles.update_one({"id": article_id}, {"$set": update_data})
    
    updated_article = await db.articles.find_one({"id": article_id})
    return Article(**updated_article)

@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str, current_user: User = Depends(get_current_user)):
    # Check if article exists and user owns it or is admin
    article = await db.articles.find_one({"id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if article['author_id'] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete this article")
    
    await db.articles.delete_one({"id": article_id})
    return {"message": "Article deleted successfully"}

# Contact Routes
@api_router.post("/contact", response_model=Contact)
async def submit_contact(contact_data: ContactCreate):
    contact_obj = Contact(**contact_data.dict())
    await db.contacts.insert_one(contact_obj.dict())
    return contact_obj

@api_router.get("/contacts", response_model=List[Contact])
async def get_contacts(current_user: User = Depends(get_current_user), status: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    
    contacts = await db.contacts.find(query).sort("created_at", -1).to_list(length=None)
    return [Contact(**contact) for contact in contacts]

@api_router.put("/contacts/{contact_id}", response_model=Contact)
async def update_contact_status(contact_id: str, contact_data: ContactUpdate, current_user: User = Depends(get_current_user)):
    contact = await db.contacts.find_one({"id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    update_data = {k: v for k, v in contact_data.dict().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc)
    
    await db.contacts.update_one({"id": contact_id}, {"$set": update_data})
    
    updated_contact = await db.contacts.find_one({"id": contact_id})
    return Contact(**updated_contact)

@api_router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, current_user: User = Depends(get_current_user)):
    contact = await db.contacts.find_one({"id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    await db.contacts.delete_one({"id": contact_id})
    return {"message": "Contact deleted successfully"}

# Dashboard Routes
@api_router.get("/dashboard/articles", response_model=List[Article])
async def get_dashboard_articles(current_user: User = Depends(get_current_user)):
    query = {}
    if current_user.role != UserRole.ADMIN:
        query["author_id"] = current_user.id
    
    articles = await db.articles.find(query).sort("created_at", -1).to_list(length=None)
    return [Article(**article) for article in articles]

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    query = {}
    if current_user.role != UserRole.ADMIN:
        query["author_id"] = current_user.id
    
    total_articles = await db.articles.count_documents(query)
    published_articles = await db.articles.count_documents({**query, "is_published": True})
    breaking_news = await db.articles.count_documents({**query, "is_breaking": True})
    
    # Contact stats
    total_contacts = await db.contacts.count_documents({})
    new_contacts = await db.contacts.count_documents({"status": "new"})
    
    # Category breakdown
    categories = {}
    for category in ArticleCategory:
        count = await db.articles.count_documents({**query, "category": category.value})
        categories[category.value] = count
    
    return {
        "total_articles": total_articles,
        "published_articles": published_articles,
        "breaking_news": breaking_news,
        "total_contacts": total_contacts,
        "new_contacts": new_contacts,
        "categories": categories
    }

# Initialize default admin user and settings on startup
@app.on_event("startup")
async def create_defaults():
    # Test MongoDB connection first
    try:
        await client.admin.command('ping')
        print(f"✅ Successfully connected to MongoDB database: {os.environ['DB_NAME']}")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("⚠️  Continuing deployment - database will be connected when available")
        return  # Skip initialization if database is not available yet
    
    # Force create default admin user (always create, even if exists)
    try:
        # Always ensure admin user exists with correct credentials
        admin_user = UserCreate(
            username="admin",
            email="admin@crewkerngazette.com",
            password="admin123",
            role=UserRole.ADMIN
        )
        hashed_password = hash_password(admin_user.password)
        user_obj = User(**admin_user.dict(exclude={'password'}))
        
        user_doc = user_obj.dict()
        user_doc['password_hash'] = hashed_password
        
        # Use upsert to always ensure admin user exists with correct password
        await db.users.update_one(
            {"username": "admin"},
            {"$set": user_doc},
            upsert=True
        )
        print("✅ Admin user created/updated: username=admin, password=admin123")
        
        # Also create backup admin
        backup_admin = UserCreate(
            username="admin_backup",
            email="backup@crewkerngazette.com", 
            password="admin123",
            role=UserRole.ADMIN
        )
        backup_hashed = hash_password(backup_admin.password)
        backup_obj = User(**backup_admin.dict(exclude={'password'}))
        backup_doc = backup_obj.dict()
        backup_doc['password_hash'] = backup_hashed
        
        await db.users.update_one(
            {"username": "admin_backup"},
            {"$set": backup_doc},
            upsert=True
        )
        print("✅ Backup admin user created/updated: username=admin_backup, password=admin123")
        
    except Exception as e:
        print(f"⚠️  Failed to create admin users: {e}")
    
    # Create default settings
    try:
        settings_exists = await db.settings.find_one()
        if not settings_exists:
            default_settings = SiteSettings()
            await db.settings.insert_one(default_settings.dict())
            print("✅ Default settings created")
        else:
            print("✅ Settings already exist")
    except Exception as e:
        print(f"⚠️  Failed to create default settings: {e}")
    
    print("🚀 Application startup completed")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()