"""
OpenAI integration for intelligent QSR assistant responses
"""

import os
import logging
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Import keyring optionally (for local development)
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class QSRAssistant:
    def __init__(self):
        """Initialize the QSR Assistant with OpenAI integration"""
        self.client = None
        self.api_key = None
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 1000
        self.temperature = 0.3
        self.demo_mode = False
        
        self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialize OpenAI client with API key from environment or keyring"""
        try:
            # Get API key from environment variable first (production)
            api_key = os.getenv("OPENAI_API_KEY")
            
            # Fallback to keyring if available (local development)
            if not api_key and KEYRING_AVAILABLE:
                api_key = keyring.get_password("memex", "OPENAI_API_KEY")
            
            if api_key:
                if api_key.startswith("demo-") or api_key == "demo":
                    # Demo mode - simulate AI responses
                    self.demo_mode = True
                    self.api_key = api_key
                    logger.info("OpenAI demo mode enabled - simulating AI responses")
                else:
                    # Real API key
                    self.client = OpenAI(api_key=api_key)
                    self.api_key = api_key
                    logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("No OpenAI API key found. AI responses will be disabled.")
                
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI integration is available"""
        return self.client is not None or self.demo_mode
    
    def create_system_prompt(self) -> str:
        """Create the beginner-friendly system prompt with SSML support for new QSR crew members"""
        return """# Lina - Your Friendly QSR Training Assistant

## **Who You Are**

You are Lina, a helpful, patient trainer speaking to brand new QSR crew members. You're like that experienced coworker who's really good at showing people the ropes. They may be nervous, learning lots of new procedures, and need clear, encouraging guidance.

Think of yourself as the friendly trainer who remembers what it was like to be new and overwhelmed. You're here to help them succeed and feel confident in their new job.

## **Your Communication Style**

**Speak like a helpful trainer, not a corporate executive:**
- Use simple, clear language that anyone can understand
- Be encouraging and patient - they're still learning
- Explain not just WHAT to do, but WHY it matters
- Give practical examples they can relate to: "like when you're making fries"
- Include SSML tags for natural, conversational speech delivery

**Your tone should be:**
- Encouraging: "You've got this!" "That's a great question!"
- Patient: "Take your time with this step" "Don't worry, this is normal"
- Practical: "You know how the fries sometimes stick? This prevents that"
- Friendly: "Okay, next up..." "Now here's the important part..."

## **Natural Speech Instructions**

Format your responses for natural speech delivery using ElevenLabs-supported features:

**Supported Tags (use sparingly):**
- Use `<break time="0.5s"/>` for pauses between steps (max 3 seconds)
- Use `<phoneme alphabet="cmu" ph="PHONETIC">word</phoneme>` for technical terms if needed

**Natural Language Approaches:**
- Use natural punctuation: periods, commas, dashes for pacing
- Write conversationally: "Okay, first thing..." "Here's what you need to know"
- Use capitalization sparingly for emphasis: "SUPER important"
- Use ellipses for hesitation: "So... let's try this"
- Use dashes for natural pauses: "First step — turn off the equipment"

**Example Natural Speech:**
"Alright, <break time="0.5s"/> let's start with the basics. Turn off the equipment first — safety is super important here. Take your time with this step."

## **Document-Based Help**

**When you have training manuals or documents:**
- Use them as your main source of information
- Quote the important parts simply: "According to the fryer manual..."
- Break down complex procedures into simple steps
- Always mention safety points from the manuals

**When you don't have specific documents:**
- Be honest: "I don't have the specific manual for that, but here's what usually works..."
- Give general best practices that are safe and common
- Suggest they check with their manager for specific procedures

## **How to Help New Crew Members**

### **For Equipment Questions:**
1. **Start with safety**: Always mention safety first
2. **Simple steps**: Break it down into easy-to-follow steps  
3. **Why it matters**: Explain why each step is important
4. **Encourage questions**: "Any questions about that step?"
5. **Be reassuring**: "This gets easier with practice"

### **For Procedures:**
1. **Set expectations**: "This might seem like a lot at first, but you'll get it"
2. **Step-by-step**: Use numbered lists and clear instructions
3. **Common mistakes**: "A lot of new people forget this part, so don't worry if you do too"
4. **Practice tips**: "The best way to remember this is..."

## **Language Guidelines**

**AVOID executive/expert language:**
- "Leverage operational frameworks"
- "Strategic implementation" 
- "Optimize performance metrics"
- "Stakeholder alignment"
- Complex business terminology

**USE beginner-friendly language:**
- "Here's how to do this"
- "Let's try this step"
- "This will help you"
- "You'll get the hang of it"
- Simple, everyday words

## **Safety Communication**

**For safety instructions:**
- Always emphasize safety naturally: "Safety first!" or "Listen carefully here"
- Explain WHY safety rules exist: "We do this because it keeps everyone safe"
- Use natural pacing: "Let me walk you through this slowly" 
- Give clear warnings: "NEVER stick your hand in the fryer!" or "Important warning"

## **Response Structure**

**For simple questions:**
1. **Friendly acknowledgment**: "Great question!"
2. **Simple answer**: Clear, direct response with natural pacing
3. **Why it matters**: Brief explanation of importance
4. **Encouragement**: "You're doing fine!"

**For complex procedures:**
1. **Reassurance**: "Don't worry, I'll walk you through this"
2. **Overview**: "Here's what we're going to do"
3. **Step-by-step**: Numbered steps with natural pauses using `<break>`
4. **Safety reminders**: Clear, emphasized safety points using natural language
5. **Practice encouragement**: "This gets easier with practice"

## **Your Mission**

Help new QSR crew members feel confident, safe, and successful in their new job. Remember - they're not executives or experts. They're real people who might be working their first job or learning a completely new industry.

Be the trainer you would have wanted when you were new - patient, encouraging, and genuinely helpful. Use natural conversational language and pacing to sound like you're right there helping them learn. Avoid complex markup - let your word choice and natural rhythm create the friendly, supportive tone."""
    
    def format_context(self, relevant_chunks: List[Dict]) -> str:
        """Format the relevant document chunks into context for OpenAI"""
        if not relevant_chunks:
            return "No relevant manual content found."
        
        context_parts = ["MANUAL CONTEXT:\n"]
        
        for i, chunk in enumerate(relevant_chunks, 1):
            filename = chunk['metadata']['filename']
            text = chunk['text']
            similarity = chunk['similarity']
            
            context_parts.append(f"Source {i} - {filename} (relevance: {similarity:.2f}):")
            context_parts.append(f"{text}\n")
        
        return "\n".join(context_parts)
    
    async def generate_response(self, user_question: str, relevant_chunks: List[Dict]) -> Dict:
        """
        Generate an AI response based on user question and relevant document context
        
        Args:
            user_question: The user's question
            relevant_chunks: List of relevant document chunks from search
            
        Returns:
            Dict with response, source info, and metadata
        """
        if not self.is_available():
            return self._fallback_response(user_question, relevant_chunks)
        
        # Handle demo mode
        if self.demo_mode:
            return self._generate_demo_response(user_question, relevant_chunks)
        
        try:
            # Format context from document search
            context = self.format_context(relevant_chunks)
            
            # Create messages for OpenAI
            messages = [
                {"role": "system", "content": self.create_system_prompt()},
                {"role": "user", "content": f"Question: {user_question}\n\n{context}"}
            ]
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            ai_response = response.choices[0].message.content
            
            # Add source attribution
            sources = []
            for chunk in relevant_chunks:
                source_info = {
                    'filename': chunk['metadata']['filename'],
                    'similarity': chunk['similarity']
                }
                if source_info not in sources:
                    sources.append(source_info)
            
            return {
                'response': ai_response,
                'type': 'ai_powered',
                'sources': sources,
                'model_used': self.model,
                'chunks_used': len(relevant_chunks)
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._fallback_response(user_question, relevant_chunks, error=str(e))
    
    async def generate_response_stream(self, user_question: str, relevant_chunks: List[Dict]):
        """
        Generate a streaming AI response based on user question and relevant document context
        
        Args:
            user_question: The user's question
            relevant_chunks: List of relevant document chunks from search
            
        Yields:
            Dict with streaming content chunks
        """
        if not self.is_available() or self.demo_mode:
            # For non-streaming cases, yield the full response at once
            full_response = await self.generate_response(user_question, relevant_chunks)
            yield {"chunk": full_response['response'], "done": True, "metadata": full_response}
            return
        
        try:
            # Format context from document search
            context = self.format_context(relevant_chunks)
            
            # Create messages for OpenAI
            messages = [
                {"role": "system", "content": self.create_system_prompt()},
                {"role": "user", "content": f"Question: {user_question}\n\n{context}"}
            ]
            
            # Call OpenAI API with streaming
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True
            )
            
            # Stream response chunks
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    yield {"chunk": content, "done": False}
            
            # Send completion signal with metadata
            sources = []
            for chunk in relevant_chunks:
                source_info = {
                    'filename': chunk['metadata']['filename'],
                    'similarity': chunk['similarity']
                }
                if source_info not in sources:
                    sources.append(source_info)
            
            yield {
                "chunk": "",
                "done": True,
                "metadata": {
                    'type': 'ai_powered',
                    'sources': sources,
                    'model_used': self.model,
                    'chunks_used': len(relevant_chunks)
                }
            }
            
        except Exception as e:
            logger.error(f"OpenAI streaming API error: {e}")
            # Fallback to regular response
            fallback_response = self._fallback_response(user_question, relevant_chunks, error=str(e))
            yield {"chunk": fallback_response['response'], "done": True, "metadata": fallback_response}
    
    def _fallback_response(self, user_question: str, relevant_chunks: List[Dict], error: Optional[str] = None) -> Dict:
        """Generate fallback response when OpenAI is not available"""
        if relevant_chunks:
            # Format manual content without AI processing
            response_parts = ["Based on your uploaded manuals:\n"]
            
            for i, chunk in enumerate(relevant_chunks, 1):
                filename = chunk['metadata']['filename']
                text = chunk['text']
                similarity = chunk['similarity']
                
                response_parts.append(f"📖 From {filename} (relevance: {similarity:.2f}):")
                response_parts.append(f"{text}\n")
            
            response_parts.append("\nNote: For more detailed AI-powered assistance, please configure an OpenAI API key.")
            response_text = "\n".join(response_parts)
            
        else:
            response_text = f"I searched through your manuals but couldn't find specific information about '{user_question}'. Try asking about equipment maintenance, cleaning procedures, or troubleshooting steps."
            if error:
                response_text += f"\n\nNote: AI enhancement temporarily unavailable ({error[:50]}...)."
        
        return {
            'response': response_text,
            'type': 'document_search_only',
            'sources': [{'filename': chunk['metadata']['filename'], 'similarity': chunk['similarity']} for chunk in relevant_chunks],
            'chunks_used': len(relevant_chunks)
        }
    
    def _generate_demo_response(self, user_question: str, relevant_chunks: List[Dict]) -> Dict:
        """Generate a demo AI response to showcase the functionality"""
        if not relevant_chunks:
            return self._fallback_response(user_question, relevant_chunks)
        
        # Create a simulated AI-style response based on the context
        context_text = " ".join([chunk['text'] for chunk in relevant_chunks])
        
        # Generate response based on question type
        if any(word in user_question.lower() for word in ['fryer', 'heat', 'oil', 'temperature']):
            demo_response = self._generate_fryer_demo_response(context_text)
        elif any(word in user_question.lower() for word in ['grill', 'clean', 'cleaning']):
            demo_response = self._generate_grill_demo_response(context_text)
        elif any(word in user_question.lower() for word in ['maintenance', 'schedule', 'daily', 'weekly']):
            demo_response = self._generate_maintenance_demo_response(context_text)
        else:
            # Generic response
            demo_response = f"""Based on your equipment manuals, here's what I found regarding "{user_question}":

The manual information shows specific procedures and guidelines for this situation. Let me break this down into actionable steps:

1. **First, ensure safety** - Always follow proper safety protocols before beginning any maintenance or troubleshooting.

2. **Check the basics** - Verify power connections, settings, and that all components are properly in place.

3. **Follow the manual procedures** - The uploaded documentation contains specific step-by-step instructions for this type of issue.

4. **When in doubt, consult the full manual** - For detailed specifications and safety warnings, refer to the complete equipment documentation.

⚠️ **Safety Note**: Always ensure equipment is properly shut down and cooled before performing any maintenance procedures.

This is a simulated AI response demonstrating how the system would provide structured, actionable guidance based on your uploaded manuals."""

        sources = []
        for chunk in relevant_chunks:
            source_info = {
                'filename': chunk['metadata']['filename'],
                'similarity': chunk['similarity']
            }
            if source_info not in sources:
                sources.append(source_info)

        return {
            'response': demo_response,
            'type': 'ai_powered_demo',
            'sources': sources,
            'model_used': 'demo-gpt-3.5-turbo',
            'chunks_used': len(relevant_chunks)
        }
    
    def _generate_fryer_demo_response(self, context: str) -> str:
        """Generate a demo response for fryer-related questions"""
        return """Based on your fryer manual, here's the troubleshooting approach for heating issues:

🔧 **Immediate Checks:**
1. **Power Connection** - Verify the fryer is properly plugged in and receiving power
2. **Circuit Breaker** - Check that the circuit breaker hasn't tripped
3. **Thermostat Settings** - Ensure temperature is set correctly

🔍 **Component Inspection:**
1. **Heating Elements** - Inspect for damage, corrosion, or burnt connections
2. **Temperature Sensor** - Clean and check for proper positioning
3. **Control Panel** - Verify all indicators are functioning normally

⚡ **Safety Priorities:**
- Turn off power before any inspection
- Allow oil to cool completely before handling
- Never attempt electrical repairs without proper training

🛠️ **Next Steps:**
If these basic checks don't resolve the issue, the heating elements may need replacement. Contact your equipment service provider for professional repair.

**Note:** This is a demonstration of AI-enhanced responses. The actual system would provide even more specific guidance based on your exact equipment model and manual content."""
    
    def _generate_grill_demo_response(self, context: str) -> str:
        """Generate a demo response for grill-related questions"""
        return """Based on your grill maintenance manual, here's the proper cleaning procedure:

📋 **Daily End-of-Service Cleaning:**
1. **Cool Down** - Turn off grill and allow to reach safe temperature (under 200°F)
2. **Remove Components** - Take out cooking grates and drip pans
3. **Scrape Surface** - Remove grease and food debris from cooking surface
4. **Clean Grates** - Use grill brush and approved degreasing solution

🧽 **Deep Cleaning Steps:**
1. **Disassembly** - Remove all removable internal components
2. **Soak Parts** - Clean removable parts in degreasing solution
3. **Wipe Surfaces** - Clean interior walls with approved cleaning agents
4. **Sanitize** - Apply sanitizing solution to all surfaces

✅ **Quality Check:**
- Ensure all cleaning solution is completely removed
- Check that all components are properly reassembled
- Verify gas connections are secure (if applicable)

⚠️ **Safety Reminders:**
- Never use water on hot surfaces
- Always use approved cleaning chemicals only
- Wear protective equipment when handling degreasers

**Note:** This AI-powered response demonstrates how the system interprets your manual content to provide structured, actionable guidance."""
    
    def _generate_maintenance_demo_response(self, context: str) -> str:
        """Generate a demo response for maintenance-related questions"""
        return """Based on your equipment manuals, here's the maintenance schedule breakdown:

📅 **Daily Tasks:**
- Check equipment operation and settings
- Clean and sanitize all surfaces
- Monitor performance indicators
- Document any issues or irregularities

📅 **Weekly Tasks:**
- Deep clean all removable components
- Inspect safety systems and connections
- Check calibration of temperature controls
- Review and update maintenance logs

📅 **Monthly Tasks:**
- Replace filters and disposable components
- Detailed inspection of electrical connections
- Calibrate sensors and control systems
- Professional service check (if due)

📊 **Documentation:**
Keep detailed records of:
- Daily cleaning completion
- Any issues or irregularities observed
- Parts replacements and repairs
- Service dates and technician notes

🎯 **Benefits of Following Schedule:**
- Extends equipment lifespan
- Maintains food safety standards
- Reduces unexpected breakdowns
- Ensures optimal performance

**Note:** This demonstrates how AI processes your maintenance manuals to create structured, easy-to-follow guidance tailored to your specific equipment."""

# Global assistant instance
qsr_assistant = QSRAssistant()