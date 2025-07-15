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
        self.model = "gpt-4"  # Much better instruction following than gpt-3.5-turbo
        self.max_tokens = 500  # Shorter responses = simpler language
        self.temperature = 0.2  # Lower temperature for more consistent instruction following
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
    
    def create_qsr_employee_system_prompt(self, simplified_context: str = "") -> str:
        """Generate system prompt optimized for QSR floor employees based on world-class expertise"""
        
        return f"""You are Line Lead, a world-class QSR expert who talks like a helpful coworker. You have the knowledge of industry leaders, successful operators, and top consultants - but you explain things like you're helping a friend at work.

CORE MISSION: Help QSR floor workers (cooks, cashiers, cleaners) get things done right with clear, simple instructions they can use immediately.

CRITICAL COMMUNICATION RULES:
- Talk like a helpful coworker, not a manager or trainer
- Use words a 7th grader would understand
- Keep sentences under 15 words
- Explain step-by-step like you're showing someone in person
- Focus on what they need to do RIGHT NOW
- Be encouraging and supportive, never preachy

TEMPERATURE INSTRUCTION GUIDELINES:
- When mentioning temperatures, use simple formats
- Instead of "350-375°F (175-190°C)" say "350 degrees" or "about 350 degrees"  
- Avoid temperature ranges unless absolutely necessary
- Use "hot oil" or "medium-high heat" when possible
- Only give specific temperatures when critical for safety

LANGUAGE RULES - MANDATORY:
BANNED WORDS (never use these):
- "Implementation," "utilize," "facilitate," "optimize," "strategic"
- "Procedures," "protocols," "specifications," "parameters"
- "Ensure," "maintain," "establish," "conduct," "verify"
- "Subsequently," "furthermore," "therefore," "comprehensive"
- Any business jargon or words over 3 syllables

USE THESE SIMPLE WORDS INSTEAD:
- "Do this" not "implement this"
- "Use" not "utilize"
- "Help" not "facilitate" 
- "Make sure" not "ensure"
- "Keep" not "maintain"
- "Check" not "verify"
- "Start" not "initiate"

DOCUMENT-FIRST APPROACH:
Your uploaded restaurant manuals are the most important source. When you have document information:
- Quote the exact steps from the manual
- Say which manual or page you're getting it from
- If multiple documents say different things, mention both
- Always use the document info first, then add your expertise

RESPONSE STRUCTURE - EVERY TIME:
1. Quick answer first (what to do right now)
2. Step-by-step instructions from the manuals
3. Safety reminder if needed (keep it simple)
4. What to watch for or check
5. "Let me know if you need help with anything else"

EXPERTISE AREAS (explain simply):
- Kitchen work: cooking, cleaning, equipment, food safety
- Customer service: taking orders, handling problems, being friendly
- Equipment: how to use it, clean it, when something's wrong
- Safety: staying safe, keeping food safe, following rules
- Teamwork: working together, helping others, communication

CLARIFICATION QUESTIONS (when unclear):
Ask simple, direct questions:
- Equipment problems: "What equipment? What's wrong with it? When did it start?"
- Cleaning questions: "What are you trying to clean? What do you usually use?"
- Food safety: "What food? How long has it been out? What temperature?"

Keep questions short and focused on what you need to know to help them.

CONTEXT FROM YOUR RESTAURANT'S MANUALS (already simplified):
{simplified_context}

REMEMBER: You're helping someone who's busy, maybe stressed, and needs an answer they can use right away. You have world-class expertise, but you share it like the helpful coworker everyone wishes they had. Make their job easier, not harder."""

    def create_voice_system_prompt(self, simplified_context: str = "") -> str:
        """Voice-optimized system prompt for QSR floor employees"""
        
        base_prompt = self.create_qsr_employee_system_prompt(simplified_context)
        
        voice_additions = """

VOICE-SPECIFIC RULES (for spoken responses):
- Keep responses under 80 words total
- Use very short sentences that are easy to follow when listening
- Pause between steps by using periods, not commas
- Say "First... Next... Then..." clearly between steps
- Avoid complex punctuation that sounds weird when spoken
- End with a simple question like "Does that help?" or "Make sense?"
- If giving more than 3 steps, break into smaller chunks

VOICE RESPONSE EXAMPLE:
"Turn off the fryer first. Wait for it to cool down completely. Then drain the oil into the waste container. Take out the baskets and wash them in the sink. Check for any stuck food bits. Does that help?"

Remember: People can't remember long spoken instructions. Keep it short and clear."""
        
        return base_prompt + voice_additions

    def create_system_prompt(self) -> str:
        """Create the default employee-friendly system prompt"""
        return self.create_qsr_employee_system_prompt()
    
    async def generate_voice_response(self, user_question: str, relevant_chunks: List[Dict]) -> Dict:
        """Generate response optimized for voice/audio output"""
        if not self.is_available():
            return self._fallback_response(user_question, relevant_chunks)
        
        # Handle demo mode
        if self.demo_mode:
            return self._generate_demo_response(user_question, relevant_chunks)
        
        try:
            # Format context from document search
            context = self.format_context(relevant_chunks)
            
            # Use voice-optimized system prompt
            system_prompt = self.create_voice_system_prompt(context)
            
            # Simple, direct user message
            user_message = user_question
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            print(f"DEBUG: Voice system prompt first 200 chars: {self.create_voice_system_prompt(context)[:200]}")
            
            # Call OpenAI API with voice-optimized settings
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=120,  # Shorter for voice
                temperature=0.3   # Lower for more consistent voice output
            )
            
            ai_response = response.choices[0].message.content
            
            # Extract source information
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
                'sources': sources,
                'model_used': self.model,
                'chunks_used': len(relevant_chunks),
                'type': 'voice_optimized'
            }
            
        except Exception as e:
            logger.error(f"OpenAI voice API error: {e}")
            return self._fallback_response(user_question, relevant_chunks, error=str(e))


    
    def format_context(self, relevant_chunks: List[Dict]) -> str:
        """Format the relevant document chunks as casual, friendly knowledge"""
        if not relevant_chunks:
            return "I don't have specific info about that, but I'll help however I can!"
        
        # Extract and simplify the content
        simplified_info = []
        for chunk in relevant_chunks:
            # Handle both old and new chunk formats
            text = chunk.get('text', chunk.get('content', ''))
            
            # Skip empty chunks
            if not text:
                continue
                
            # Simplify corporate language in the content
            simplified_text = self._simplify_manual_text(text)
            simplified_info.append(simplified_text)
        
        # Format as casual knowledge sharing
        unique_info = list(set(simplified_info))  # Remove duplicates
        if len(unique_info) == 1:
            return f"Here's what I learned in training: {unique_info[0]}"
        else:
            context_parts = ["Here's what I remember from training:"]
            for info in unique_info[:2]:  # Limit to 2 most relevant
                context_parts.append(f"- {info}")
            return "\n".join(context_parts)
    
    def _simplify_manual_text(self, text: str) -> str:
        """Convert formal manual language to casual, friendly terms"""
        # Replace technical/corporate terms with simple alternatives
        replacements = {
            'equipment': 'machine',
            'personnel': 'workers',
            'utilize': 'use',
            'implement': 'do',
            'procedure': 'steps',
            'protocol': 'way to do it',
            'maintenance': 'cleaning',
            'deactivate': 'turn off',
            'activate': 'turn on',
            'optimal': 'best',
            'ensure': 'make sure',
            'verify': 'check',
            'apparatus': 'machine',
            'initiate': 'start',
            'terminate': 'stop',
            'sufficient': 'enough',
            'comprehensive': 'complete'
        }
        
        simplified = text.lower()
        for formal, casual in replacements.items():
            simplified = simplified.replace(formal, casual)
        
        # Remove corporate formatting markers
        simplified = simplified.replace('section ', '').replace('§', '')
        simplified = simplified.replace('manual context:', '')
        simplified = simplified.replace('source 1 -', '').replace('source 2 -', '')
        
        # Make it sound conversational
        if not simplified.endswith('.'):
            simplified += '.'
            
        return simplified.strip().capitalize()
    
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
            # Format context from document search as casual knowledge
            context = self.format_context(relevant_chunks)
            
            # Use QSR employee-optimized system prompt with manual context embedded
            system_prompt = self.create_qsr_employee_system_prompt(context)
            
            # Simple, direct user message (context is now in system prompt)
            user_message = user_question
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Call OpenAI API with strengthened parameters
            print(f"DEBUG: Using model: {self.model}, temp: {self.temperature}")
            print(f"DEBUG: System prompt first 100 chars: {self.create_system_prompt()[:100]}")
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
                # Handle both old and new chunk formats
                if 'metadata' in chunk and 'filename' in chunk['metadata']:
                    # Old format
                    source_info = {
                        'filename': chunk['metadata']['filename'],
                        'similarity': chunk.get('similarity', chunk.get('score', 0.0))
                    }
                else:
                    # New format from main.py
                    source_info = {
                        'filename': chunk.get('source', 'Unknown'),
                        'similarity': chunk.get('score', 0.0)
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
            # Format context from document search as casual knowledge
            context = self.format_context(relevant_chunks)
            
            # Use QSR employee-optimized system prompt with manual context embedded
            system_prompt = self.create_qsr_employee_system_prompt(context)
            
            # Simple, direct user message (context is now in system prompt)
            user_message = user_question
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Call OpenAI API with streaming and strengthened parameters
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
        """Generate a demo response for fryer-related questions using simplified language"""
        return """Great question! Here's how to clean the fryer safely:

**Safety first!** Turn off the fryer and let it cool down for 30-40 minutes. Hot oil can burn you.

Here's what to do:

1. **Turn off the fryer**
   Unplug it from the wall

2. **Wait for it to cool down**  
   This takes about 30-40 minutes
   Don't touch the oil yet!

3. **Put on safety glasses**
   The manual says to always wear them

4. **Cover the fryer with trays**
   This keeps the oil clean

5. **Use the right cleaner**
   Use only approved degreaser 
   Follow the directions on the bottle

6. **Clean it step by step**
   Spray the cleaner on
   Wipe it down with a towel
   Make sure you get all the grease off

**Remember:** Never use wet rags on hot oil. Always let it cool first.

You've got this! Cleaning gets easier with practice. Ask your manager if you need help the first few times.

This keeps your fryer working great and the food tasting good!"""
    
    def _generate_grill_demo_response(self, context: str) -> str:
        """Generate a demo response for grill-related questions using simplified language"""
        return """Good question! Here's how to clean the grill:

**First - safety!** Let the grill cool down to under 200 degrees. Hot metal can burn you.

**Daily cleaning steps:**

1. **Turn off the grill**
   Make sure it's cooling down

2. **Take out the parts**
   Remove the cooking grates
   Take out the drip pans

3. **Scrape off the food bits**
   Use the grill scraper
   Get all the leftover food off

4. **Clean the grates**
   Use the grill brush
   Spray them with degreaser
   Scrub until they're clean

**For deep cleaning:**

1. **Take everything apart** 
   Remove all the parts you can

2. **Soak the parts**
   Put them in soapy water
   Let them sit for a few minutes

3. **Wipe down the inside**
   Use approved cleaner only
   Get all the grease off the walls

4. **Put it back together**
   Make sure everything fits right
   Check that gas connections are tight

**Remember:** Never spray water on a hot grill! Always let it cool first.

Don't worry if this seems like a lot. You'll get faster at it. Ask for help if you need it!"""
    
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