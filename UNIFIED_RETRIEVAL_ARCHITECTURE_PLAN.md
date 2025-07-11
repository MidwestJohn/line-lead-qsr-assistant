# 🏗️ **UNIFIED RETRIEVAL ARCHITECTURE PLAN**

## **🎯 PROBLEM STATEMENT**

**Current Architecture Issue**: Text and voice use separate retrieval paths with inconsistent quality.

```
❌ CURRENT (Dual Architecture):
Text Input  → rag_service.py → Poor retrieval → Generic answers
Voice Input → voice_graph_service.py → Good retrieval → Quality answers

✅ TARGET (Unified Architecture):  
Text Input  ┐
           ├→ Unified Retrieval System → Neo4j + Multi-modal → Quality Answers
Voice Input ┘
```

---

## **📊 CURRENT STATE ANALYSIS**

### **Voice Service (Working Well) ✅**
- **Path**: `voice_agent.py` → `voice_graph_query_service.py` → `enhanced_document_retrieval_service.py`
- **Capabilities**:
  - Multi-modal Neo4j queries across ALL documents
  - Enhanced document retrieval with relevance scoring
  - LLM integration with proper context formatting
  - Temperature queries return specific equipment manual content
  - Visual citations and page references preserved

### **Text Chat Service (Broken/Inconsistent) ❌**
- **Path**: Unknown/multiple rag services
- **Issues**:
  - Generic responses instead of specific equipment details
  - Poor Neo4j integration
  - Missing multi-modal enhancements
  - Inconsistent retrieval quality

---

## **🔍 SUCCESS FACTORS FROM VOICE SERVICE**

### **1. Multi-Modal Neo4j Queries**
```cypher
// Voice service uses enhanced queries across ALL documents
MATCH (n)
WHERE (
    n.name CONTAINS "temperature" OR 
    n.name CONTAINS "safety" OR 
    n.name CONTAINS "procedure"
)
RETURN n.name, n.description, n.visual_refs, n.page_refs, n.document_source
ORDER BY size(coalesce(n.visual_refs, [])) DESC
```

### **2. Enhanced Document Retrieval**
- Searches ALL uploaded PDFs (Taylor C602, fryer, grill manuals)
- Relevance scoring based on keyword matching
- Fallback mechanisms when LightRAG unavailable
- Content chunking with context preservation

### **3. Proper LLM Integration**
- Enhanced context formatting for conversational responses
- Raw content synthesis into natural language
- Equipment-specific context awareness
- Page references and visual citations included

---

## **🏗️ UNIFICATION STRATEGY**

### **Phase 1: Extract Core Retrieval Logic**

#### **1.1 Create Unified Retrieval Service**
```python
# services/unified_retrieval_service.py
class UnifiedRetrievalService:
    """Single retrieval system for both text and voice inputs"""
    
    def __init__(self):
        self.neo4j_service = neo4j_service
        self.document_retrieval = enhanced_document_retrieval_service
        self.voice_graph_service = VoiceGraphQueryService(neo4j_service)
    
    async def process_query(self, query: str, input_type: str = "text") -> Dict:
        """Unified query processing for text and voice"""
        # Use voice service's proven logic
        result = await self.voice_graph_service.process_voice_query_with_graph_context(
            query, session_id=f"{input_type}_session"
        )
        return self._normalize_result(result, input_type)
```

#### **1.2 Normalize Response Format**
```python
def _normalize_result(self, result: Dict, input_type: str) -> Dict:
    """Convert voice service result to format suitable for text/voice"""
    return {
        "response_text": result.get("response", ""),
        "source_content": result.get("source_content", []),
        "page_references": result.get("page_references", []),
        "visual_citations": result.get("visual_citations", []),
        "equipment_context": result.get("equipment_context"),
        "multimodal_enhanced": result.get("multimodal_enhanced", False),
        "input_type": input_type
    }
```

### **Phase 2: Refactor Input Layer Separation**

#### **2.1 Text Input Handler**
```python
# text_input_handler.py
async def process_text_message(message: str, session_id: str) -> Dict:
    """Process text input through unified retrieval"""
    
    # Use unified retrieval (voice service logic)
    result = await unified_retrieval_service.process_query(
        query=message,
        input_type="text"
    )
    
    # Apply text-specific formatting if needed
    return {
        "text_response": result["response_text"],
        "visual_citations": result["visual_citations"],
        "page_references": result["page_references"],
        "source": "unified_retrieval"
    }
```

#### **2.2 Voice Input Handler**
```python
# voice_input_handler.py  
async def process_voice_message(message: str, session_id: str) -> Dict:
    """Process voice input through unified retrieval"""
    
    # Use same unified retrieval
    result = await unified_retrieval_service.process_query(
        query=message,
        input_type="voice"
    )
    
    # Apply voice-specific formatting (TTS optimization)
    return {
        "text_response": optimize_for_speech(result["response_text"]),
        "audio_response": await text_to_speech(result["response_text"]),
        "visual_citations": result["visual_citations"],
        "source": "unified_retrieval"
    }
```

### **Phase 3: API Endpoint Unification**

#### **3.1 Main Chat Endpoint Update**
```python
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Unified chat endpoint for text input"""
    
    # Route through unified retrieval
    result = await text_input_handler.process_text_message(
        message=request.message,
        session_id=request.session_id
    )
    
    return ChatResponse(
        response=result["text_response"],
        visual_citations=result["visual_citations"],
        page_references=result["page_references"],
        enhanced=True
    )
```

#### **3.2 Voice Endpoint Update**
```python
@app.post("/api/voice")
async def voice_endpoint(request: VoiceRequest):
    """Unified voice endpoint"""
    
    # Route through unified retrieval (same logic as text)
    result = await voice_input_handler.process_voice_message(
        message=request.transcript,
        session_id=request.session_id
    )
    
    return VoiceResponse(
        text_response=result["text_response"],
        audio_response=result["audio_response"],
        visual_citations=result["visual_citations"]
    )
```

---

## **🔧 IMPLEMENTATION STEPS**

### **Step 1: Analysis Phase**
1. **Audit current text chat path** - identify which files handle text retrieval
2. **Document voice service components** - map working voice architecture
3. **Identify shared dependencies** - Neo4j service, document storage, LLM integration
4. **Performance baseline** - test current voice service quality vs text chat quality

### **Step 2: Extraction Phase**
1. **Create UnifiedRetrievalService** - extract voice service logic
2. **Generalize session management** - remove voice-specific assumptions
3. **Standardize response format** - common structure for text/voice results
4. **Test extraction** - ensure unified service maintains voice service quality

### **Step 3: Integration Phase**
1. **Update text chat endpoints** - route through unified retrieval
2. **Refactor voice endpoints** - use unified retrieval with TTS layer
3. **Remove duplicate services** - deprecate old rag_service.py or similar
4. **Update frontend** - ensure text chat uses enhanced responses

### **Step 4: Validation Phase**
1. **A/B testing** - compare unified vs old text responses
2. **Voice regression testing** - ensure voice quality maintained
3. **Load testing** - verify performance with unified architecture
4. **User acceptance testing** - validate both input methods work identically

---

## **📊 EXPECTED BENEFITS**

### **Immediate Improvements**
- ✅ **Text chat quality** matches voice service quality
- ✅ **Consistent responses** across input methods
- ✅ **Multi-modal support** for text chat (visual citations, page refs)
- ✅ **Equipment-specific answers** for text queries

### **Long-term Benefits**
- ✅ **Single codebase** for retrieval logic
- ✅ **Easier maintenance** - fix once, improves both paths
- ✅ **Better testing** - unified test suite
- ✅ **Faster feature development** - implement once for both interfaces

---

## **🧪 SUCCESS METRICS**

### **Quality Metrics**
- Text query: "What temperature for Taylor C602?" → Specific equipment temps
- Voice query: Same question → Identical answer content
- Response time: <3 seconds for both text and voice
- Accuracy: Equipment manuals properly referenced

### **Technical Metrics**
- Code duplication: Eliminate separate retrieval services
- Test coverage: Single test suite covers both input paths
- Performance: No degradation in voice service quality
- Maintainability: Single point of enhancement for both interfaces

---

## **⚠️ RISKS & MITIGATION**

### **Risk 1: Voice Service Regression**
- **Mitigation**: Extensive regression testing, feature flags
- **Rollback Plan**: Keep voice service backup during transition

### **Risk 2: Performance Impact**
- **Mitigation**: Load testing, performance monitoring
- **Optimization**: Caching layer, async processing

### **Risk 3: API Breaking Changes**
- **Mitigation**: Backward compatibility layer
- **Strategy**: Gradual migration with parallel endpoints

---

## **🎯 IMMEDIATE NEXT STEPS**

1. **Audit Current Text Path** (30 minutes)
   - Find files handling text chat retrieval
   - Document current text response quality issues
   - Identify integration points

2. **Extract Voice Logic** (2 hours)
   - Create unified_retrieval_service.py
   - Generalize voice_graph_query_service.py logic
   - Test extraction maintains quality

3. **Implement Text Integration** (1 hour)
   - Route text chat through unified retrieval
   - Update main chat endpoint
   - Test text queries for improvement

4. **Validation Testing** (1 hour)
   - Compare text vs voice responses for same queries
   - Verify multi-modal features work in text chat
   - Performance testing

---

## **💬 DISCUSSION POINTS**

1. **Which specific files currently handle text chat retrieval?**
2. **Are there text-specific features that need preservation?**
3. **Should we implement gradual migration or full replacement?**
4. **What are the most critical text queries to test during migration?**

---

**🎯 GOAL: One retrieval system, consistent quality, maintainable architecture**

**🤖 Generated with [Memex](https://memex.tech)**  
**Co-Authored-By: Memex <noreply@memex.tech>**