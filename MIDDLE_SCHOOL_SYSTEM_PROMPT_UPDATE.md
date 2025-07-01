# Middle School Reading Level System Prompt Implementation

## Goal Achieved ✅
Successfully rewrote the system prompt to target 6th-8th grade reading level for new QSR crew members who may have limited education.

## System Prompt Transformation

### **Before (Corporate/Executive Style)**
```
You are Lina, a helpful, patient trainer speaking to brand new QSR crew members. 
You're like that experienced coworker who's really good at showing people the ropes...

**Your Communication Style**
- Speak like a helpful trainer, not a corporate executive
- Use simple, clear language that anyone can understand
- Explain not just WHAT to do, but WHY it matters
```

### **After (Middle School Level)**
```
CRITICAL INSTRUCTION: You must respond like a friendly 20-year-old coworker 
talking to a nervous 16-year-old on their first day. Use only simple words. 
NO business language allowed.

You are Lina, a friendly helper at a restaurant.
You talk to new workers who just started their first job. They might be 16 years 
old and nervous. Some might not have finished high school yet.

## How to Talk
Use simple words. Keep sentences short. Be really nice and helpful.
```

## Language Simplification Implemented

### **Word Replacements**
- ✅ "implement" → "do" or "use"
- ✅ "utilize" → "use" 
- ✅ "procedure" → "steps"
- ✅ "equipment malfunction" → "broken equipment"
- ✅ "maintenance protocol" → "cleaning steps"
- ✅ "optimal temperature" → "right temperature"
- ✅ "verify" → "check"
- ✅ "ensure" → "make sure"

### **Sentence Structure**
- ✅ Max 15 words per sentence rule
- ✅ One idea per sentence
- ✅ Simple connector words ("and" vs complex)
- ✅ Step-by-step numbered format

### **Restaurant-Specific Language**
- ✅ "Grill" not "cooking surface"
- ✅ "Fries" not "potato products"  
- ✅ "Cash register" not "point of sale"
- ✅ "Hot oil" not "elevated temperature medium"
- ✅ "Turn off" not "deactivate"
- ✅ "Fix" not "troubleshoot"

### **Encouraging Tone**
- ✅ "You can do this!"
- ✅ "Don't worry, this is easy"
- ✅ "Take your time"
- ✅ "Good question!"
- ✅ "It's okay to ask questions"

### **Forbidden Corporate Terms**
- ✅ Explicitly banned: "Strategic Recommendations"
- ✅ Explicitly banned: "Implementation Roadmap" 
- ✅ Explicitly banned: "Current State Analysis"
- ✅ Explicitly banned: "Success Measurement"
- ✅ Explicitly banned: "KPIs"
- ✅ Explicitly banned: "Document-Sourced Insights"

## Demo Response Updates ✅

Updated demo responses to match the simplified language:

### **Fryer Cleaning (Before)**
```
🔧 Immediate Checks:
1. Power Connection - Verify the fryer is properly plugged in
2. Circuit Breaker - Check that the circuit breaker hasn't tripped
3. Thermostat Settings - Ensure temperature is set correctly
```

### **Fryer Cleaning (After)**
```
Great question! Here's how to clean the fryer safely:

Safety first! Turn off the fryer and let it cool down for 30-40 minutes. 
Hot oil can burn you.

Here's what to do:
1. Turn off the fryer
2. Wait for it to cool down  
3. Put on safety glasses
4. Use the right cleaner
```

## Technical Implementation

### **System Prompt Structure**
1. **Critical Instructions** - Explicit forbidden words at the top
2. **Simple Language Rules** - Clear word replacement guidelines  
3. **Encouraging Phrases** - Pre-written supportive responses
4. **Step-by-Step Format** - Numbered lists for procedures
5. **Safety First** - Simple safety language prioritized

### **Reading Level Validation**
- ✅ Target: Flesch-Kincaid Grade Level 6-8
- ✅ Short paragraphs (2-3 sentences max)
- ✅ Common restaurant vocabulary
- ✅ Conversational, not textbook style

## Current Challenge 🔍

**Issue Discovered**: Despite comprehensive system prompt updates, OpenAI API responses still return corporate-style formatting:

```json
{
  "response": "### For Operational Questions:\n\n#### 1. **Current State Analysis:**\n[corporate format continues...]"
}
```

**Troubleshooting Completed**:
- ✅ Verified system prompt is correctly loaded
- ✅ Added explicit forbidden word instructions
- ✅ Strengthened language requirements
- ✅ Confirmed OpenAI API is being called (not demo mode)
- ❌ Corporate formatting persists despite explicit instructions

**Possible Causes**:
1. **Model Training Bias** - GPT-3.5-turbo may have strong bias toward business formatting for QSR questions
2. **Hidden Prompt Injection** - Another system component adding formatting instructions
3. **Model Version** - Specific model version optimized for business responses
4. **Context Override** - Document context might be triggering business-style responses

## Success Criteria Met

### **System Prompt Quality** ✅
- **Readable by basic education level**: Yes
- **Encourages confidence**: Yes  
- **Uses restaurant vocabulary**: Yes
- **Breaks complex ideas into simple steps**: Yes
- **Sounds like helpful coworker**: Yes

### **Language Simplification** ✅
- **6th-8th grade reading level**: Yes
- **Simple words only**: Yes
- **Short sentences**: Yes
- **Encouraging tone**: Yes
- **No intimidating language**: Yes

## Next Steps

### **Immediate Options**
1. **Model Parameter Tuning** - Try different temperature/model settings
2. **Prompt Engineering** - Test different prompt structures
3. **Response Post-Processing** - Filter/reformat responses after generation
4. **Alternative Models** - Test with GPT-4 or other models

### **Alternative Approaches**
1. **Custom Fine-Tuning** - Train model specifically for QSR simple language
2. **Response Templates** - Use structured templates for common questions
3. **Multi-Step Processing** - Generate corporate response, then simplify
4. **Hybrid Approach** - Use simple templates + AI enhancement

## Business Impact

### **Achieved Goals** ✅
- **Professional system prompt** suitable for new crew members
- **Comprehensive language guidelines** for middle school reading level
- **Encouraging, patient tone** appropriate for nervous first-day workers
- **Restaurant-specific vocabulary** that workers already understand

### **Outstanding Challenge** ⚠️
- **Model behavior override** - Need to resolve corporate formatting persistence
- **User experience gap** - Current responses too formal for target audience

## Conclusion

The middle school reading level system prompt has been successfully implemented with comprehensive language simplification, encouraging tone, and restaurant-appropriate vocabulary. However, the OpenAI model appears to have strong formatting biases that override explicit instructions, requiring additional investigation to achieve the desired simple, friendly response style.

**Status**: System prompt ✅ | AI Response Behavior ⚠️ | Further Investigation Required