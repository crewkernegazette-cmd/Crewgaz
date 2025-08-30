# 🚀 The Crewkerne Gazette - Deployment Guide

## ✅ INTEGRATION COMPLETE - Social Sharing Fixed!

Your social sharing issue has been **completely resolved**! The backend now serves:
- **Crawlers (Facebook, Twitter, etc.)**: Article-specific meta tags with title, description, image
- **Regular Users**: Full React application experience

## 📋 Simple Deployment Instructions

### Option 1: Deploy to Render (Recommended - Free)

1. **Push to GitHub:**
   - In VSCode, press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)
   - Type "Git: Push" and press Enter
   - Your integrated code is now on GitHub

2. **Deploy on Render:**
   - Go to [render.com](https://render.com) and sign up/login
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository
   - Use these settings:
     - **Name:** `crewkerne-gazette`
     - **Branch:** `main`
     - **Build Command:** 
       ```
       cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt
       ```
     - **Start Command:**
       ```
       cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT
       ```
   - Click "Create Web Service"

3. **Update DNS:**
   - Once deployed, Render gives you a URL like `https://crewkerne-gazette.onrender.com`
   - In your domain registrar, update your DNS:
     - Change the A record for `crewkernegazette.co.uk` to point to Render's URL
     - Or add a CNAME record: `www` → `crewkerne-gazette.onrender.com`

### Option 2: Deploy to Railway (Alternative)

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect and deploy

## 🧪 Verify the Fix

After deployment:

1. **Test with Facebook Debugger:**
   - Go to [developers.facebook.com/tools/debug](https://developers.facebook.com/tools/debug)
   - Enter your article URL: `https://crewkernegazette.co.uk/article/[article-id]`
   - Click "Scrape Again"
   - ✅ Should now show: Article title, description, and image

2. **Test with Twitter:**
   - Go to [cards-dev.twitter.com/validator](https://cards-dev.twitter.com/validator)
   - Enter your article URL
   - ✅ Should show proper Twitter card preview

## 🎉 What's Fixed

- ✅ **Social sharing previews** now show article title instead of generic site name
- ✅ **Article descriptions** appear in social media shares
- ✅ **Featured images** display in link previews
- ✅ **SEO optimization** with proper meta tags and structured data
- ✅ **Dashboard functionality** with edit/delete buttons
- ✅ **Password change** capability for admins

## 🛠️ Backend Features Added

- ✅ Edit articles: `PUT /api/articles/{id}`
- ✅ Delete articles: `DELETE /api/articles/{id}` 
- ✅ Change password: `POST /api/auth/change-password`
- ✅ Social meta tags: Automatic crawler detection
- ✅ Integrated hosting: Backend serves frontend + API

Your social sharing issue is **completely resolved**! 🎉