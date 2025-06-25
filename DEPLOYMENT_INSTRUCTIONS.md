# 🚀 Production Deployment Instructions

## ✅ GitHub Repository
**Repository URL**: https://github.com/MidwestJohn/line-lead-qsr-assistant
**Status**: ✅ Created and code pushed successfully

---

## 🖥️ Backend Deployment - Render

### Step 1: Create Render Service
1. Go to https://dashboard.render.com/
2. Click "New Web Service"
3. Connect your GitHub account if not already connected
4. Select repository: `MidwestJohn/line-lead-qsr-assistant`

### Step 2: Configure Service Settings
```
Name: line-lead-qsr-backend
Branch: main
Region: Oregon (US West) or your preferred region
Build Command: cd backend && pip install -r requirements.txt
Start Command: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Step 3: Set Environment Variables
```
OPENAI_API_KEY = [Your OpenAI API Key - provided separately for security]

CORS_ORIGINS = https://line-lead-qsr-assistant.vercel.app,http://localhost:3000

PYTHON_VERSION = 3.11
```

### Step 4: Advanced Settings
- **Health Check Path**: `/health`
- **Plan**: Starter (free tier)
- **Auto-Deploy**: Yes (deploy on git push)

**Expected Backend URL**: `https://line-lead-qsr-backend.onrender.com`

---

## 🌐 Frontend Deployment - Vercel

### Step 1: Install GitHub Integration
1. Go to https://github.com/apps/vercel
2. Install Vercel GitHub App
3. Grant access to the `line-lead-qsr-assistant` repository

### Step 2: Create Vercel Project
1. Go to https://vercel.com/dashboard
2. Click "New Project"
3. Import from GitHub: `MidwestJohn/line-lead-qsr-assistant`

### Step 3: Configure Project Settings
```
Framework Preset: Create React App
Build Command: npm run build
Output Directory: build
Install Command: npm install
```

### Step 4: Set Environment Variables
```
REACT_APP_API_URL = https://line-lead-qsr-backend.onrender.com
```

### Step 5: Deploy
- Click "Deploy" to build and deploy
- Vercel will automatically deploy on every git push to main

**Expected Frontend URL**: `https://line-lead-qsr-assistant.vercel.app`

---

## 🔄 Deployment Sequence

### 1. Deploy Backend First (Render)
Deploy the backend service first to get the production API URL.

### 2. Update Frontend Environment
Update the `REACT_APP_API_URL` in Vercel to point to your actual Render backend URL.

### 3. Deploy Frontend (Vercel)
Deploy the frontend with the correct backend URL.

### 4. Update CORS
Update the backend's `CORS_ORIGINS` environment variable in Render to include your actual Vercel frontend URL.

---

## ✅ Success Verification

### Backend Health Check
```bash
curl https://your-backend-url.onrender.com/health
```
Should return:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-24T...",
  "services": {
    "database": "ready",
    "search_engine": "ready", 
    "ai_assistant": "ready",
    "file_upload": "ready"
  }
}
```

### Frontend Test
1. Visit your Vercel URL
2. Test chat functionality
3. Test file upload
4. Verify mobile responsiveness

### End-to-End Test
1. Upload a PDF manual
2. Ask a question about equipment maintenance
3. Verify AI responds with relevant information

---

## 🔧 Post-Deployment Configuration

### Automatic Deployments
Both platforms are configured for automatic deployment:
- **Render**: Deploys backend on every push to `main`
- **Vercel**: Deploys frontend on every push to `main`

### Monitoring
- **Render**: Built-in metrics and logs
- **Vercel**: Analytics and deployment logs
- **Backend Health**: `/health` endpoint monitoring

### Scaling
- **Render**: Can upgrade from Starter to paid plans
- **Vercel**: Automatic scaling included

---

## 🚨 Important Notes

1. **First Deploy**: Backend may take 5-10 minutes to start (free tier)
2. **Cold Starts**: Render free tier has ~30 second cold start delay
3. **HTTPS**: Both platforms provide automatic HTTPS
4. **Custom Domain**: Can be configured in both platforms
5. **Environment Updates**: Require redeployment

---

## 📞 Support URLs

- **GitHub Repository**: https://github.com/MidwestJohn/line-lead-qsr-assistant
- **Render Dashboard**: https://dashboard.render.com/
- **Vercel Dashboard**: https://vercel.com/dashboard
- **API Documentation**: `https://your-backend-url.onrender.com/docs`

---

## 🔑 Security Note

The OpenAI API key and other sensitive credentials are provided separately and should be configured directly in the deployment platform environment variables for security.