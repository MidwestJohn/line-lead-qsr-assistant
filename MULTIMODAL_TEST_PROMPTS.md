# 🎨 **MULTI-MODAL TEST PROMPTS**

## **🧪 Test Prompts for Visual Reference Validation**

Based on the Neo4j analysis, here are specific test prompts that should return visual references from the uploaded "New Crew Handbook":

---

## **🌡️ TEMPERATURE-RELATED QUERIES** (High Confidence)

### **Prompt 1: Temperature Procedures**
```
"What are the temperature requirements for food safety?"
```

**Expected Results:**
- ✅ Text response about temperature procedures
- ✅ Visual citations linked to temperature entities
- ✅ Page references: [9, 2, 98, 1]
- ✅ Visual citation IDs: 436a62f0, dfa1e1f1, 3f98ec96, 8ca95b41

### **Prompt 2: Temperature Monitoring**
```
"How do I check and monitor temperatures properly?"
```

**Expected Results:**
- ✅ Temperature monitoring procedures
- ✅ Visual references to temperature charts/tables
- ✅ Page citations from the crew handbook

---

## **📋 PROCEDURE-RELATED QUERIES** (Medium Confidence)

### **Prompt 3: Safety Procedures**
```
"What are the safety procedures I need to follow?"
```

**Expected Results:**
- ✅ Safety procedure text
- ✅ Visual references (4 items)
- ✅ Page references: [9, 2, 98, 1]
- ✅ Related to safety warnings and procedures

### **Prompt 4: Cleaning Procedures**
```
"Show me the cleaning procedures and guidelines."
```

**Expected Results:**
- ✅ Cleaning procedure steps
- ✅ Visual citations (4 items)
- ✅ Page references from manual
- ✅ Maintenance and service procedures

### **Prompt 5: Equipment Maintenance**
```
"What maintenance procedures do I need to follow for equipment?"
```

**Expected Results:**
- ✅ Maintenance procedure text
- ✅ Equipment-related visual references
- ✅ Service and procedure citations

---

## **🔧 EQUIPMENT-RELATED QUERIES** (Medium Confidence)

### **Prompt 6: Equipment Guide**
```
"Where can I find the equipment guide and instructions?"
```

**Expected Results:**
- ✅ Equipment guide information
- ✅ Visual references (3 items)
- ✅ Page references: [9, 2, 1]
- ✅ Manual and equipment citations

### **Prompt 7: Tools and Equipment**
```
"What tools do I need and how do I use them?"
```

**Expected Results:**
- ✅ Tool usage information
- ✅ Equipment-related visual references
- ✅ Step-by-step procedures

---

## **📍 LOCATION-RELATED QUERIES** (Lower Confidence)

### **Prompt 8: Storage Procedures**
```
"Where should I store items and what are the storage procedures?"
```

**Expected Results:**
- ✅ Storage location information
- ✅ Storage procedure guidelines
- ✅ Location-specific visual references

### **Prompt 9: Workspace Layout**
```
"Can you show me the front counter and back area procedures?"
```

**Expected Results:**
- ✅ Counter and workspace information
- ✅ Front/back area procedures
- ✅ Location-specific visual citations

---

## **🔍 COMPREHENSIVE TEST QUERIES**

### **Prompt 10: Complete Procedure Overview**
```
"I'm a new employee. Can you give me a complete overview of procedures, safety guidelines, and equipment I need to know about?"
```

**Expected Results:**
- ✅ Comprehensive response covering multiple entities
- ✅ Multiple visual citations from different categories
- ✅ Temperature, safety, cleaning, and equipment references
- ✅ Page citations from throughout the manual

### **Prompt 11: Step-by-Step Guide**
```
"Walk me through the step-by-step procedures for opening and operating safely."
```

**Expected Results:**
- ✅ Step-by-step procedures
- ✅ Visual references to procedural steps
- ✅ Safety warning citations
- ✅ Equipment and method references

---

## **📊 TESTING METHODOLOGY**

### **What to Look For:**

1. **Visual Citation Integration:**
   - Check if responses include "See page X" references
   - Look for visual citation IDs in response metadata
   - Verify page references match Neo4j data

2. **Multi-Modal Enhancement Indicators:**
   - Responses should be richer with supporting visual context
   - Should reference specific pages from the manual
   - May include temperature charts, procedure diagrams, safety visuals

3. **Entity Linking:**
   - Temperature queries should link to temperature entities
   - Procedure queries should connect to procedure entities
   - Equipment queries should reference equipment guides

### **Success Criteria:**

- ✅ **Visual References**: Responses include page numbers and visual citations
- ✅ **Enhanced Context**: Answers are more comprehensive with visual support
- ✅ **Accurate Citations**: Page references match uploaded document
- ✅ **Multi-Modal Integration**: System leverages visual content alongside text

---

## **🎯 RECOMMENDED TEST SEQUENCE**

1. **Start with Temperature Queries** (highest confidence for visual references)
2. **Test Safety and Cleaning Procedures** (good visual citation coverage)
3. **Try Equipment and Tool Queries** (equipment guide references)
4. **Test Comprehensive Queries** (multiple visual citations)
5. **Verify Page References** (check if cited pages make sense)

---

## **📈 EXPECTED IMPROVEMENTS**

**Before Multi-Modal:**
- Text-only responses
- No visual context
- Missing procedural diagrams

**After Multi-Modal:**
- Text + visual citations
- Page-specific references
- Complete context with supporting visuals
- Professional QSR manual experience

---

**🎨 Ready to test the multi-modal integration! Try these prompts in the frontend and look for enhanced responses with visual citations and page references.**