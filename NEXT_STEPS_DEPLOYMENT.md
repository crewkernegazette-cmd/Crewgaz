# 🚀 Deployment Guide for PostgreSQL Version

## ✅ Current Status: Task 1 Complete

**PostgreSQL Integration**: ✅ Complete and tested locally

## 📋 To Deploy Task 1 (PostgreSQL) to Render:

### Step 1: Push to GitHub
1. In VSCode: `Ctrl+Shift+P` → "Git: Push"
2. Commit message: "Add PostgreSQL database integration with persistent storage"

### Step 2: Add PostgreSQL to Render
1. Go to your Render dashboard
2. Click "New +" → "PostgreSQL"  
3. Name: `crewkerne-gazette-db`
4. Plan: Free tier
5. Click "Create Database"
6. **Save the DATABASE_URL** provided (looks like: `postgresql://user:pass@host/db`)

### Step 3: Update Backend Service
1. Go to your web service in Render
2. Go to "Environment" tab
3. Add new environment variable:
   - **Key**: `DATABASE_URL`
   - **Value**: The PostgreSQL URL from step 2
4. Click "Save Changes"

### Step 4: Deploy
1. Go to "Manual Deploy" → "Deploy latest commit"
2. Wait for deployment to complete
3. Check logs for "✅ Database initialized successfully"

### Step 5: Test Production
1. Visit your site: `https://crewkernegazette.co.uk`
2. Login to dashboard: admin/admin123
3. Create a test article
4. Verify it persists after refreshing

## 🔄 For Tasks 2 & 3 (Cloudinary + SEO):

**Task 2 - Cloudinary Integration:**
- Need Cloudinary account credentials
- Will replace base64 images with cloud storage
- Will fix social sharing images completely

**Task 3 - SEO Enhancements:**
- Add sitemaps for Google News
- Enhance structured data
- Add robots.txt

## 📞 What You Need to Provide:

**For Cloudinary (Task 2):**
```
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key  
CLOUDINARY_API_SECRET=your-api-secret
```

Get these from: cloudinary.com (free tier available)

## 🎯 Expected Results After Task 1 Deployment:

- ✅ Articles persist between deployments
- ✅ No more data loss on server restarts
- ✅ Professional database-backed CMS
- ✅ Better performance with indexed queries
- ✅ Ready for scaling and backups

**The foundation is solid - ready to build Tasks 2 & 3 on top!** 🚀