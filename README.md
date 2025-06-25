# Line Lead QSR Assistant 🍟

A mobile-first AI assistant for Quick Service Restaurant (QSR) workers, providing instant help with equipment maintenance by intelligently searching uploaded equipment manuals.

## 🚀 Quick Start

### Setup OpenAI (Optional)
For enhanced AI responses, set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```
Or use demo mode:
```bash
export OPENAI_API_KEY="demo"
```

### Run Both Services
```bash
# Option 1: Use the start script
./start_dev.sh

# Option 2: Manual start
# Terminal 1 - Backend
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend  
npm start
```

## 📱 Access URLs

- **Local (Computer)**: http://localhost:3000
- **iPhone/Mobile**: http://192.168.1.241:3000 (replace with your IP)
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

## 🏗️ Architecture

### Frontend (React)
- Mobile-first responsive design
- Real-time chat interface
- Loading states and error handling
- PWA capabilities

### Backend (FastAPI)
- RESTful API with CORS enabled
- Health check endpoint
- Structured logging
- Error handling

## 🧪 Testing

### Test Chat API
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I clean the grill?"}'
```

### Test File Upload
```bash
curl -X POST -F "file=@your_manual.pdf" http://localhost:8000/upload
```

### Test Document List
```bash
curl http://localhost:8000/documents
```

### Test Health Check
```bash
curl http://localhost:8000/health
```

### Test Document Search
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I fix my fryer that won'\''t heat oil?"}'
```

### Test AI Status
```bash
curl http://localhost:8000/ai-status
```

### Test Search Statistics
```bash
curl http://localhost:8000/search-stats
```

### Test AI Responses
```bash
./test_ai_responses.sh
```

### Run All Tests
```bash
./test_upload.sh
./test_search.sh
./test_ai_responses.sh
```

## 📋 Current Features

✅ Mobile-optimized chat interface  
✅ FastAPI backend with CORS  
✅ Real-time message processing  
✅ Loading states and error handling  
✅ Health monitoring  
✅ Network access for mobile testing  
✅ **PDF file upload and processing**  
✅ **Text extraction from equipment manuals**  
✅ **Document management and listing**  
✅ **File validation (PDF only, 10MB limit)**  
✅ **Drag & drop upload interface**  
✅ **🧠 Intelligent document search with embeddings**  
✅ **📝 Text chunking and semantic similarity**  
✅ **🔍 Contextual chat responses from manuals**  
✅ **⚡ Real-time document indexing**  
✅ **🎯 Relevance-based result filtering**  
✅ **🤖 AI-powered responses with OpenAI integration**  
✅ **📋 Structured, actionable guidance with safety notes**  
✅ **💡 Smart formatting with step-by-step procedures**  
✅ **🔄 Graceful fallback when AI unavailable**  
✅ **📊 AI status monitoring and demo mode**  

## 🛠️ Tech Stack

- **Frontend**: React, CSS3, PWA, Drag & Drop API
- **Backend**: FastAPI, Uvicorn, PyPDF2
- **AI/ML**: Sentence Transformers, OpenAI GPT-3.5-turbo, Embeddings, Cosine Similarity
- **File Processing**: PDF text extraction, Text chunking, JSON storage
- **Search**: Semantic search with all-MiniLM-L6-v2 model
- **Intelligence**: AI-powered responses, structured guidance, safety integration
- **Development**: Hot reload, CORS enabled, File validation, Demo mode

## 📝 Development Notes

- Backend runs on port 8000
- Frontend runs on port 3000
- CORS configured for local and network access
- All responses are currently mock responses
- Ready for AI integration in next build

## 🔄 Next Steps

- [x] Add file upload capability
- [x] Extract text from PDF manuals
- [x] Store document metadata
- [x] **Implement semantic document search**
- [x] **Add vector embeddings for text chunks**
- [x] **Connect chat responses to uploaded manual content**
- [x] **Integrate OpenAI API for intelligent responses**
- [x] **Add structured, actionable AI guidance**
- [x] **Implement safety-focused response formatting**
- [ ] Add conversation memory/context
- [ ] Add multi-language support
- [ ] Deploy to cloud platform (AWS/GCP/Azure)