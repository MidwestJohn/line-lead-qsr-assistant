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

    def create_system_prompt(self) -> str:
        """Create a purely positive system prompt with simple language requirements"""
        return """You are Lina, a friendly 20-year-old restaurant worker helping a nervous new employee on their first day.

RESPONSE FORMAT - Always respond exactly like this:

Start with: "Good question!" or "Don't worry!" or "You've got this!"

Then explain in simple steps:
1. First step (use simple words)
2. Next step (keep it short)
3. Last step (be encouraging)

Example response style:
"Good question! Here's how to clean the fryer.

First, turn off the fryer. Unplug it from the wall.
Next, wait 30 minutes for it to cool down. Hot oil burns!
Then, put on your safety glasses. Spray cleaner on it.
Last, wipe it clean with a towel. You're doing great!

Safety tip: Always let equipment cool first. This keeps you safe."

LANGUAGE RULES:
- Use words a 16-year-old knows
- Keep sentences under 15 words
- Be encouraging and patient
- Give safety tips
- Explain why steps matter

Remember: You're helping someone who might be scared and new. Be the coworker you'd want on your first day. Use simple restaurant words they already know.

**Use words like this:**
- "do" not "implement" 
- "use" not "utilize"
- "steps" not "procedure"
- "broken" not "malfunction"
- "right temperature" not "optimal temperature"
- "turn off" not "deactivate"
- "check" not "verify"
- "fix" not "troubleshoot"

**Talk like this:**
- "You can do this!"
- "Don't worry, this is easy"
- "Take your time"
- "Good question!"
- "You've got this"
- "Let me help you"

## Keep It Simple

**Short sentences only.** Max 15 words each.

Bad: "You need to make sure that you check the temperature before you start cooking because if it's not hot enough the food won't cook right."

Good: "Check the temperature first. Make sure it's hot enough. This helps the food cook right."

**One idea per sentence.**

Bad: "Turn off the fryer and unplug it and then clean it with soap."

Good: "Turn off the fryer. Unplug it. Then clean it with soap."

## Restaurant Words

Use words they already know:
- "Grill" not "cooking surface"  
- "Fries" not "potato products"
- "Cash register" not "point of sale"
- "Drive-thru" not "service window"
- "Rush hour" not "peak period"
- "Hot oil" not "elevated temperature medium"

## Safety First

Always talk about safety. But keep it simple.

**Say this:** "Safety first! Turn off the machine before you clean it. Hot oil can burn you."

**Not this:** "Prior to initiating maintenance protocols, ensure all thermal regulation systems are deactivated to prevent injury."

## When They Ask Questions

**Start with:** "Great question!" or "Good thinking!"

**Then explain simply:**
1. Tell them what to do
2. Show them how 
3. Say why it matters
4. Ask if they understand

**Example:**
"Great question! Here's how to clean the grill:

1. Turn it off first
2. Let it cool down
3. Scrape off the food bits  
4. Wipe it clean

We do this so the next food tastes good. Make sense?"

## Step by Step Help

Break everything into small steps. Number them.

**For cleaning a fryer:**
1. Turn off the fryer
2. Unplug it from the wall
3. Let the oil cool down
4. Put on gloves
5. Drain the oil into the bucket
6. Wipe down the inside
7. Wash it with soap
8. Dry it off

Say: "Don't worry if this seems like a lot. You'll get faster with practice!"

## If You Don't Know

Be honest. Say: "I don't have the manual for that machine. Ask your manager. They'll show you the right way."

## What NOT to Say

Don't use big words:
- Don't say "implement" - say "do"
- Don't say "facilitate" - say "help"  
- Don't say "apparatus" - say "machine"
- Don't say "subsequently" - say "then"
- Don't say "ensure" - say "make sure"

## Be Encouraging

Remember: They might be scared. This might be their first job ever.

Say things like:
- "It's okay to ask questions"
- "Everyone makes mistakes when they're learning"
- "You're doing great"
- "This is hard at first, but you'll get it"
- "I'm here to help"

## Your Job

Help them feel good about their new job. Keep them safe. Use words they understand. Be patient and kind.

Think about this: You're talking to someone who might be 16 and nervous about their first day at McDonald's. Use words they know. Keep it simple. Be the helpful person you'd want on your first day.

REMEMBER: 
- NO business language (no "strategic", "implementation", "analysis", etc.)
- NO numbered sections like "1. Current State Analysis"
- NO corporate formatting
- Talk like a friendly coworker, not a business consultant
- Use the manual information but explain it simply
- Be encouraging and patient"""

    def format_context(self, relevant_chunks: List[Dict]) -> str:
        """Format the relevant document chunks as casual, friendly knowledge"""
        if not relevant_chunks:
            return "I don't have specific info about that, but I'll help however I can!"

        # Extract and simplify the content
        simplified_info = []
        for chunk in relevant_chunks:
            text = chunk["text"]

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
            "equipment": "machine",
            "personnel": "workers",
            "utilize": "use",
            "implement": "do",
            "procedure": "steps",
            "protocol": "way to do it",
            "maintenance": "cleaning",
            "deactivate": "turn off",
            "activate": "turn on",
            "optimal": "best",
            "ensure": "make sure",
            "verify": "check",
            "apparatus": "machine",
            "initiate": "start",
            "terminate": "stop",
            "sufficient": "enough",
            "comprehensive": "complete",
        }

        simplified = text.lower()
        for formal, casual in replacements.items():
            simplified = simplified.replace(formal, casual)

        # Remove corporate formatting markers
        simplified = simplified.replace("section ", "").replace("§", "")
        simplified = simplified.replace("manual context:", "")
        simplified = simplified.replace("source 1 -", "").replace("source 2 -", "")

        # Make it sound conversational
        if not simplified.endswith("."):
            simplified += "."

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

            # Conversational context injection to prevent corporate language contamination
            system_prompt = self.create_system_prompt()

            # Separate style from content - frame context as casual knowledge
            if (
                context
                and "No relevant" not in context
                and "don't have specific info" not in context
            ):
                user_message = f"""I have a question about restaurant work: {user_question}

{context}

Can you help explain this in simple terms? Remember, I'm new and want to learn the right way to do things safely."""
            else:
                user_message = f"I have a question about restaurant work: {user_question}\n\nCan you help explain this simply? I'm new and want to learn the safe way to do things."

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]

            # Call OpenAI API with strengthened parameters
            print(f"DEBUG: Using model: {self.model}, temp: {self.temperature}")
            print(f"DEBUG: System prompt first 100 chars: {self.create_system_prompt()[:100]}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            ai_response = response.choices[0].message.content

            # Add source attribution
            sources = []
            for chunk in relevant_chunks:
                source_info = {
                    "filename": chunk["metadata"]["filename"],
                    "similarity": chunk["similarity"],
                }
                if source_info not in sources:
                    sources.append(source_info)

            return {
                "response": ai_response,
                "type": "ai_powered",
                "sources": sources,
                "model_used": self.model,
                "chunks_used": len(relevant_chunks),
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
            yield {"chunk": full_response["response"], "done": True, "metadata": full_response}
            return

        try:
            # Format context from document search as casual knowledge
            context = self.format_context(relevant_chunks)

            # Conversational context injection to prevent corporate language contamination
            system_prompt = self.create_system_prompt()

            # Separate style from content - frame context as casual knowledge
            if (
                context
                and "No relevant" not in context
                and "don't have specific info" not in context
            ):
                user_message = f"""I have a question about restaurant work: {user_question}

{context}

Can you help explain this in simple terms? Remember, I'm new and want to learn the right way to do things safely."""
            else:
                user_message = f"I have a question about restaurant work: {user_question}\n\nCan you help explain this simply? I'm new and want to learn the safe way to do things."

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]

            # Call OpenAI API with streaming and strengthened parameters
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
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
                    "filename": chunk["metadata"]["filename"],
                    "similarity": chunk["similarity"],
                }
                if source_info not in sources:
                    sources.append(source_info)

            yield {
                "chunk": "",
                "done": True,
                "metadata": {
                    "type": "ai_powered",
                    "sources": sources,
                    "model_used": self.model,
                    "chunks_used": len(relevant_chunks),
                },
            }

        except Exception as e:
            logger.error(f"OpenAI streaming API error: {e}")
            # Fallback to regular response
            fallback_response = self._fallback_response(
                user_question, relevant_chunks, error=str(e)
            )
            yield {
                "chunk": fallback_response["response"],
                "done": True,
                "metadata": fallback_response,
            }

    def _fallback_response(
        self, user_question: str, relevant_chunks: List[Dict], error: Optional[str] = None
    ) -> Dict:
        """Generate fallback response when OpenAI is not available"""
        if relevant_chunks:
            # Format manual content without AI processing
            response_parts = ["Based on your uploaded manuals:\n"]

            for i, chunk in enumerate(relevant_chunks, 1):
                filename = chunk["metadata"]["filename"]
                text = chunk["text"]
                similarity = chunk["similarity"]

                response_parts.append(f"📖 From {filename} (relevance: {similarity:.2f}):")
                response_parts.append(f"{text}\n")

            response_parts.append(
                "\nNote: For more detailed AI-powered assistance, please configure an OpenAI API key."
            )
            response_text = "\n".join(response_parts)

        else:
            response_text = f"I searched through your manuals but couldn't find specific information about '{user_question}'. Try asking about equipment maintenance, cleaning procedures, or troubleshooting steps."
            if error:
                response_text += (
                    f"\n\nNote: AI enhancement temporarily unavailable ({error[:50]}...)."
                )

        return {
            "response": response_text,
            "type": "document_search_only",
            "sources": [
                {"filename": chunk["metadata"]["filename"], "similarity": chunk["similarity"]}
                for chunk in relevant_chunks
            ],
            "chunks_used": len(relevant_chunks),
        }

    def _generate_demo_response(self, user_question: str, relevant_chunks: List[Dict]) -> Dict:
        """Generate a demo AI response to showcase the functionality"""
        if not relevant_chunks:
            return self._fallback_response(user_question, relevant_chunks)

        # Create a simulated AI-style response based on the context
        context_text = " ".join([chunk["text"] for chunk in relevant_chunks])

        # Generate response based on question type
        if any(word in user_question.lower() for word in ["fryer", "heat", "oil", "temperature"]):
            demo_response = self._generate_fryer_demo_response(context_text)
        elif any(word in user_question.lower() for word in ["grill", "clean", "cleaning"]):
            demo_response = self._generate_grill_demo_response(context_text)
        elif any(
            word in user_question.lower() for word in ["maintenance", "schedule", "daily", "weekly"]
        ):
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
                "filename": chunk["metadata"]["filename"],
                "similarity": chunk["similarity"],
            }
            if source_info not in sources:
                sources.append(source_info)

        return {
            "response": demo_response,
            "type": "ai_powered_demo",
            "sources": sources,
            "model_used": "demo-gpt-3.5-turbo",
            "chunks_used": len(relevant_chunks),
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
