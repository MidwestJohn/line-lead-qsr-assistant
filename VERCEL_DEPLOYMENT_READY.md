# 🚀 Vercel Frontend Deployment - Ready to Deploy

## ✅ **Frontend Configuration Complete**

### **Environment Variables Set**
- **Production**: `REACT_APP_API_URL=https://line-lead-qsr-backend.onrender.com`
- **Development**: `REACT_APP_API_URL=http://localhost:8000`
- **Vercel Config**: Updated with production backend URL

### **Files Updated**
- ✅ `.env.production` - Production environment
- ✅ `.env.local` - Development environment  
- ✅ `vercel.json` - Vercel deployment configuration
- ✅ All API calls configured to use environment variables

---

## 🌐 **Deploy to Vercel Now**

### **Step 1: Install GitHub Integration** 
1. Go to https://github.com/apps/vercel
2. Install Vercel GitHub App
3. Grant access to `line-lead-qsr-assistant` repository

### **Step 2: Create Vercel Project**
1. Go to https://vercel.com/dashboard
2. Click **"New Project"**
3. **Import from GitHub**: `MidwestJohn/line-lead-qsr-assistant`

### **Step 3: Configure Project Settings**
```
Project Name: line-lead-qsr-assistant
Framework Preset: Create React App
Root Directory: ./ (leave as root)
Build Command: npm run build
Output Directory: build
Install Command: npm install
```

### **Step 4: Environment Variables** 
Vercel should automatically detect from `vercel.json`, but verify:
```
REACT_APP_API_URL = https://line-lead-qsr-backend.onrender.com
```

### **Step 5: Deploy**
- Click **"Deploy"** 
- Vercel will build and deploy automatically
- **Expected URL**: `https://line-lead-qsr-assistant.vercel.app`

---

## 🔧 **Post-Deployment**

### **Once Both Services Are Live:**
1. **Test Frontend**: Visit your Vercel URL
2. **Test Backend Communication**: Try the chat feature
3. **Test File Upload**: Upload a PDF manual
4. **Mobile Test**: Check responsiveness on phone

### **Expected URLs:**
- **Frontend**: `https://line-lead-qsr-assistant.vercel.app`
- **Backend**: `https://line-lead-qsr-backend.onrender.com`
- **Backend Health**: `https://line-lead-qsr-backend.onrender.com/health`
- **API Docs**: `https://line-lead-qsr-backend.onrender.com/docs`

---

## 🎯 **Deployment Status**

- ✅ **GitHub Repository**: Updated with production configuration
- ⏳ **Backend (Render)**: Deploying `https://line-lead-qsr-backend.onrender.com`
- ⏳ **Frontend (Vercel)**: Ready to deploy → `https://line-lead-qsr-assistant.vercel.app`

**Next**: Deploy frontend to Vercel using the steps above!