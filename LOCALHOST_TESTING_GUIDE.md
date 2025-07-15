# 🧪 LOCALHOST TESTING GUIDE - PydanticAI Integration

## 🚀 SERVERS RUNNING

### **Backend Server** ✅
- **URL**: http://localhost:8000
- **Version**: 3.0.0-production (Phase 3)
- **Features**: Multi-Agent Orchestration, Production Security, Performance Monitoring
- **Status**: Healthy (0% error rate)

### **Frontend Server** ✅  
- **URL**: http://localhost:3000
- **Framework**: React with Craco
- **Status**: Available and responding

## 🧪 TESTING ENDPOINTS

### **Health Checks**
```bash
# Backend health
curl http://localhost:8000/health

# System metrics
curl http://localhost:8000/metrics

# Server info
curl http://localhost:8000/info
```

### **PydanticAI Multi-Agent Chat**
```bash
# Production chat endpoint
curl -X POST http://localhost:8000/chat/production \
-H "Content-Type: application/json" \
-d '{
  "message": "Taylor E01 grill not heating properly", 
  "conversation_id": "test_session",
  "priority": "high"
}'

# Expected: Equipment agent response with troubleshooting guide
```

### **Agent Classification Testing**
```bash
# Equipment query
curl -X POST http://localhost:8000/chat/production \
-H "Content-Type: application/json" \
-d '{"message": "Vulcan fryer temperature issue"}'
# Should route to: equipment agent

# Safety query  
curl -X POST http://localhost:8000/chat/production \
-H "Content-Type: application/json" \
-d '{"message": "Employee burn injury protocol"}'
# Should route to: base agent (safety fallback)

# Operations query
curl -X POST http://localhost:8000/chat/production \
-H "Content-Type: application/json" \
-d '{"message": "Restaurant opening procedure"}'
# Should route to: base agent (operations fallback)
```

## 🎯 TESTING SCENARIOS

### **Equipment Troubleshooting**
- "Taylor E01 error code troubleshooting"
- "Hobart mixer not working properly"
- "Vulcan fryer temperature calibration"
- "Ice cream machine cleaning procedure"

### **Safety Protocols**
- "Emergency burn protocol"
- "Chemical spill procedure"  
- "Fire safety checklist"
- "First aid protocols"

### **Operations Procedures**
- "Opening checklist"
- "Closing procedures"
- "Food safety protocols"
- "Equipment maintenance schedule"

### **Training Scenarios**
- "New employee fryer training"
- "Safety training procedures"
- "Equipment operation training"
- "Customer service protocols"

## 🔍 WHAT TO TEST

### **✅ Multi-Agent Functionality**
1. **Agent Selection**: Verify equipment queries route to equipment agent
2. **Response Quality**: Check for comprehensive, detailed responses (2000-3500 chars)
3. **Processing Time**: Should be 9-19 seconds for complex queries
4. **Confidence Scoring**: Should show 0.6-0.8 confidence levels
5. **Conversation Continuity**: Test conversation_id preservation

### **✅ Production Features**
1. **Security**: Input validation with proper error messages
2. **Performance**: Response time tracking and metrics
3. **Error Handling**: Test invalid inputs for graceful degradation
4. **Rate Limiting**: Currently disabled for testing
5. **Monitoring**: Health checks and system metrics

### **✅ QSR Domain Knowledge**
1. **Equipment Recognition**: Taylor, Vulcan, Hobart equipment specificity
2. **Safety Protocols**: Emergency procedures and safety warnings
3. **Operational Procedures**: Step-by-step guidance
4. **Technical Accuracy**: Equipment-specific troubleshooting steps

### **✅ Integration Testing**
1. **Frontend ↔ Backend**: Test chat interface functionality
2. **Voice Integration**: Test voice input/output (if available)
3. **Visual Citations**: Test image display with responses
4. **Cross-Modal**: Test switching between text and voice

## 📊 PERFORMANCE EXPECTATIONS

### **Response Times**
- **Simple queries**: 5-10 seconds
- **Equipment troubleshooting**: 10-20 seconds  
- **Complex multi-step procedures**: 15-25 seconds

### **Response Quality**
- **Length**: 2000-3500 characters for detailed responses
- **Structure**: Step-by-step procedures with safety warnings
- **Technical Detail**: Equipment-specific instructions
- **Safety Focus**: Proper safety protocols included

### **System Performance**
- **Memory Usage**: ~15-17 MB (very efficient)
- **CPU Usage**: <1% (very low)
- **Error Rate**: <1% (excellent reliability)
- **Concurrent Handling**: Multiple requests supported

## 🚨 TROUBLESHOOTING

### **If Backend Not Responding**
```bash
# Check if running
ps aux | grep start_phase3_production.py

# Restart if needed
pkill -f start_phase3_production.py
python start_phase3_production.py > backend_new.log 2>&1 &
```

### **If Frontend Not Loading**
```bash
# Check port 3000
lsof -i:3000

# Restart if needed
npm start
```

### **If Chat Not Working**
1. Check backend health: `curl http://localhost:8000/health`
2. Verify OpenAI API key in environment
3. Check logs: `tail -f backend_localhost.log`

## 🎉 READY FOR TESTING!

Both servers are running with the complete PydanticAI integration:
- ✅ **Multi-Agent Orchestration** active
- ✅ **Production Security** enabled
- ✅ **Performance Monitoring** tracking
- ✅ **QSR Domain Knowledge** preserved
- ✅ **All UAT-tested features** deployed

**Start testing at**: http://localhost:3000

---

**Branch**: features/pydantic-integration  
**Generated with Memex (https://memex.tech)**