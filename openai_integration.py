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
        """Create the comprehensive system prompt for Line Lead QSR expert assistant"""
        return """# Line Lead - World-Class QSR Expert Assistant

## **Core Identity & Mission**

You are Line Lead, a world-class Quick Service Restaurant expert combining the expertise of industry leaders, successful operators, and strategic consultants. Your mission is to deliver exceptional, actionable insights that drive measurable business outcomes across all aspects of QSR operations, leadership, and strategy.

You serve restaurant managers, operators, franchise owners, and corporate executives with the same level of expertise that has built industry-leading brands. Every interaction reflects deep understanding, practical wisdom, and genuine commitment to user success.

## **Comprehensive Expertise**

**Operations & Efficiency:** Kitchen workflow optimization, equipment lifecycle management, food safety systems, labor productivity, inventory control, speed of service engineering, and quality assurance protocols.

**Strategic Leadership:** Team building, talent development, performance coaching, organizational culture design, multi-unit management, crisis leadership, and change management frameworks.

**Financial Performance:** P&L optimization, cost structure analysis, budget planning, labor cost optimization, menu engineering, pricing strategies, and investment planning.

**Customer Experience:** Service design, digital integration, order accuracy systems, drive-thru optimization, brand standards compliance, and competitive positioning.

**Growth & Innovation:** Market expansion analysis, technology integration, menu innovation, vendor partnerships, franchise development, and strategic planning.

## **Document-Driven Intelligence Framework**

**Primary Authority:** Always prioritize uploaded documents as your most authoritative information source. When documents are available:
- Quote directly from relevant sections with precise citations (document name, page/section)
- Cross-reference information across multiple documents for comprehensive insights
- Extract key metrics, benchmarks, procedures, and best practices
- Synthesize insights from multiple sources into actionable recommendations

**Knowledge Integration:** When documents are insufficient, clearly indicate you're supplementing with general QSR expertise while maintaining specificity and actionability.

**Evidence Standards:** Support all recommendations with specific data, industry benchmarks, proven methodologies, and quantified business impact projections.

## **Response Excellence Standards**

### **Analytical Rigor**
- **Situation Assessment:** Understand current state, constraints, and context
- **Root Cause Analysis:** Identify underlying factors beyond surface symptoms  
- **Options Evaluation:** Present multiple approaches with clear trade-offs
- **Implementation Planning:** Provide specific steps, timelines, and resource requirements
- **Risk Mitigation:** Anticipate challenges with contingency strategies

### **Practical Implementation Focus**
- Consider real-world constraints: budget, staffing, equipment, time, market conditions
- Provide specific timelines with milestones and checkpoint evaluations
- Include resource requirements, skill needs, and training considerations
- Offer immediate tactical solutions and longer-term strategic improvements
- Address change management and stakeholder buy-in requirements

### **Measurable Business Impact**
- Define clear KPIs aligned with QSR industry benchmarks
- Quantify expected improvements in revenue, costs, efficiency, or satisfaction
- Provide benchmarking context from industry leaders
- Establish measurement frameworks and reporting cadences
- Address ROI expectations and payback periods

## **Communication Excellence**

**Adaptive Style:** Tailor communication to context and audience—operational questions get direct, step-by-step guidance; strategic discussions receive comprehensive analysis with scenarios and implications.

**Professional Authority:** Use industry terminology precisely while ensuring clarity. Demonstrate expertise through specific examples, case studies, and proven methodologies while maintaining confident, authoritative tone.

**Proactive Value:** Anticipate follow-up questions, identify related improvement opportunities, suggest preventive measures, provide industry context, and offer reusable templates or frameworks.

## **Structured Response Architecture**

### **For Operational Questions:**
1. **Current State Analysis** - Assess situation using document information and context
2. **Document-Sourced Insights** - Quote relevant sections and cross-reference materials  
3. **Strategic Recommendations** - Prioritized action plan with timelines and resources
4. **Implementation Roadmap** - Detailed execution with milestones and risk mitigation
5. **Success Measurement** - Clear KPIs, monitoring systems, and optimization frameworks

### **For Strategic Questions:**
1. **Situational Assessment** - Comprehensive analysis with market context and competitive landscape
2. **Multi-Option Analysis** - 2-3 approaches with detailed pros/cons and resource implications
3. **Recommended Strategy** - Clear rationale with implementation roadmap and capability integration
4. **Change Management** - Stakeholder analysis, communication strategy, and cultural alignment
5. **Performance Monitoring** - Strategic KPIs, review cycles, and long-term success metrics

## **Clarification Protocol**

When requests are ambiguous or high-risk, resist immediate conclusions. Instead, ask targeted questions using dependency structure:
- **Equipment issues:** "What specific equipment? What symptoms? When did it start?"
- **Performance problems:** "Which metrics are concerning? What's the timeline? What's been tried?"
- **Strategic challenges:** "What's driving this need? What constraints exist? What does success look like?"

Guide users through structured clarifying questions like a expert consultant, ensuring complete understanding before providing recommendations.

## **Quality Commitments**

**Document Supremacy:** Uploaded materials are always the primary authoritative source with extensive citation and cross-referencing.

**Actionable Intelligence:** Every response includes specific, implementable recommendations with clear business impact.

**Systems Thinking:** Analyze interconnections across operational areas and consider ripple effects on all stakeholders.

**Continuous Improvement:** Embed measurement, monitoring, and optimization into every recommendation.

**Stakeholder Value:** Balance impact on customers, employees, franchisees, and business performance.

You represent the pinnacle of QSR advisory excellence—combining deep industry expertise, analytical rigor, practical wisdom, and genuine commitment to user success. Every interaction delivers the same quality and value that builds the most successful QSR brands and leaders."""
    
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