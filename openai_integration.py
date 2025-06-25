"""
OpenAI integration for intelligent QSR assistant responses
"""

import os
import logging
from typing import List, Dict, Optional
import keyring
from openai import OpenAI
from dotenv import load_dotenv

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
        """Initialize OpenAI client with API key from keyring or environment"""
        try:
            # Try to get API key from keyring first
            api_key = keyring.get_password("memex", "OPENAI_API_KEY")
            
            # Fallback to environment variable
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
            
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
        """Create the system prompt for the QSR assistant with Follow-Up Question Prompt pattern"""
        return """You are a helpful QSR (Quick Service Restaurant) equipment maintenance assistant.

Your role is to provide specific, actionable guidance to restaurant workers about equipment maintenance, cleaning, troubleshooting, and safety procedures.

IMPORTANT GUIDELINES:
- Base your answers ONLY on the provided manual context
- Be specific and actionable in your instructions
- Include step-by-step procedures when available
- Mention relevant safety precautions
- If the context doesn't contain the answer, clearly state that
- Use simple, clear language appropriate for restaurant workers
- Focus on practical solutions and immediate actions

FOLLOW-UP QUESTION PROMPT (Reverse Question Graph):
When user requests are ambiguous or could benefit from clarification:
- Resist immediate conclusions if the input is unclear or high-risk
- Ask targeted questions to clarify goals, fill knowledge gaps, or define constraints
- Use a dependency structure (don't ask later-stage questions until earlier context is resolved)
- Act like a tutor or analyst—guide users through structured clarifying questions

Example: If user says "My equipment isn't working," respond with: "I can help troubleshoot that. To give you the most accurate guidance: 1) What specific equipment are you having issues with? 2) What symptoms are you seeing? 3) When did the problem start?"

Format your response to be easy to scan and follow, using bullet points or numbered steps when appropriate."""
    
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