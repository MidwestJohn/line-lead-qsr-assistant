"""
ElevenLabs Voice Service for Line Lead QSR MVP
Optimized to eliminate chunking issues and weird pauses
"""

import logging
import os
import asyncio
import httpx
import time
import tempfile
import base64
from typing import Dict, Optional, List
from fastapi import HTTPException
import re

logger = logging.getLogger(__name__)

class ElevenLabsVoiceService:
    """Optimized voice service that eliminates chunking and pause issues"""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
        self.model_id = "eleven_monolingual_v1"  # Most stable model for accurate numbers
        
        # ENHANCED Rachel voice settings to reduce temperature artifacts
        self.voice_settings = {
            "stability": 0.85,       # INCREASED for temperature numbers
            "similarity_boost": 0.55, # SLIGHTLY REDUCED from 0.6
            "style": 0.05,          # REDUCED from 0.1 for cleaner speech
            "speaking_rate": 0.95   # SLIGHTLY SLOWER for clarity
        }
        
        # Rate limiting to prevent API throttling issues
        self.last_request_time = 0
        self.min_request_interval = 1.5  # Minimum 1.5 seconds between requests
        self.is_processing = False
        
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY not found in environment variables")
    
    def is_available(self) -> bool:
        """Check if ElevenLabs service is available"""
        return bool(self.api_key)
    
    def clean_text_for_speech(self, text: str) -> str:
        """Enhanced text optimization with temperature and number range handling"""
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code
        text = re.sub(r'#{1,6}\s', '', text)          # Headers
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
        
        # Basic cleanup
        optimized = text.replace("...", ".")
        optimized = optimized.replace("  ", " ")
        optimized = optimized.replace("\n\n", "\n")
        optimized = re.sub(r'\n+', '. ', optimized)
        
        # CRITICAL FIX: Handle temperature ranges properly
        # Convert temperature ranges to natural speech
        optimized = re.sub(r'(\d+)-(\d+)°F', r'\1 to \2 degrees Fahrenheit', optimized)
        optimized = re.sub(r'(\d+)-(\d+)°C', r'\1 to \2 degrees Celsius', optimized)
        optimized = re.sub(r'(\d+)°F', r'\1 degrees Fahrenheit', optimized)
        optimized = re.sub(r'(\d+)°C', r'\1 degrees Celsius', optimized)
        
        # Convert common cooking temperatures to natural pronunciation
        optimized = re.sub(r'\b350\b', 'three hundred and fifty', optimized)
        optimized = re.sub(r'\b375\b', 'three hundred and seventy-five', optimized)
        optimized = re.sub(r'\b325\b', 'three hundred and twenty-five', optimized)
        optimized = re.sub(r'\b400\b', 'four hundred', optimized)
        optimized = re.sub(r'\b425\b', 'four hundred and twenty-five', optimized)
        optimized = re.sub(r'\b450\b', 'four hundred and fifty', optimized)
        optimized = re.sub(r'\b300\b', 'three hundred', optimized)
        
        # Convert Celsius equivalents
        optimized = re.sub(r'\b175\b', 'one hundred and seventy-five', optimized)
        optimized = re.sub(r'\b190\b', 'one hundred and ninety', optimized)
        optimized = re.sub(r'\b200\b', 'two hundred', optimized)
        optimized = re.sub(r'\b220\b', 'two hundred and twenty', optimized)
        optimized = re.sub(r'\b230\b', 'two hundred and thirty', optimized)
        optimized = re.sub(r'\b180\b', 'one hundred and eighty', optimized)
        
        # Handle parenthetical temperature conversions more naturally
        optimized = re.sub(r'\(([^)]+)\)', r'or \1', optimized)
        
        # Convert numbered lists to spelled-out format
        optimized = re.sub(r'\b1\.', 'First.', optimized)
        optimized = re.sub(r'\b2\.', 'Second.', optimized)
        optimized = re.sub(r'\b3\.', 'Third.', optimized)
        optimized = re.sub(r'\b4\.', 'Fourth.', optimized)
        optimized = re.sub(r'\b5\.', 'Fifth.', optimized)
        optimized = re.sub(r'\b6\.', 'Sixth.', optimized)
        optimized = re.sub(r'\b7\.', 'Seventh.', optimized)
        optimized = re.sub(r'\b8\.', 'Eighth.', optimized)
        
        # Fix common abbreviations
        optimized = optimized.replace("e.g.", "for example")
        optimized = optimized.replace("i.e.", "that is")
        optimized = optimized.replace("etc.", "and so on")
        optimized = optimized.replace("vs.", "versus")
        optimized = optimized.replace("w/", "with")
        optimized = optimized.replace("&", "and")
        
        # Handle degree symbols that might cause issues
        optimized = optimized.replace("°", " degrees ")
        optimized = re.sub(r'\s+', ' ', optimized)  # Clean up multiple spaces
        
        # Ensure proper ending
        if not optimized.endswith(('.', '!', '?')):
            optimized += "."
        
        return optimized.strip()
    
    async def get_voice_status(self) -> Dict:
        """Get ElevenLabs service status and available voices"""
        if not self.api_key:
            return {
                "available": False,
                "error": "API key not configured"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/voices",
                    headers={"xi-api-key": self.api_key},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    voices_data = response.json()
                    return {
                        "available": True,
                        "voice_count": len(voices_data.get("voices", [])),
                        "current_voice": "Rachel",
                        "voice_id": self.voice_id
                    }
                else:
                    return {
                        "available": False,
                        "error": f"API returned status {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"ElevenLabs status check failed: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    async def generate_audio_safely(self, text: str, retries: int = 3) -> Optional[bytes]:
        """ENHANCED audio generation with diagnostic logging"""
        if not self.api_key:
            logger.error("ElevenLabs API key not configured")
            return None
        
        # DIAGNOSTIC: Log the exact text being sent
        logger.info(f"🎙️ EXACT TEXT TO ELEVENLABS: '{text}'")
        logger.info(f"🎙️ TEXT LENGTH: {len(text)} characters")
        logger.info(f"🎙️ TEXT REPR: {repr(text)}")  # Shows hidden characters
        
        # Check for corruption patterns
        if ".." in text:
            logger.warning(f"🚨 FOUND DOUBLE PERIODS in text: {text}")
        if "  " in text:
            logger.warning(f"🚨 FOUND DOUBLE SPACES in text: {text}")
        if text.endswith("..."):
            logger.warning(f"🚨 TEXT ENDS WITH ELLIPSIS: {text}")
        
        # CRITICAL: Rate limiting to prevent throttling
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        
        # Clean and optimize text for speech
        clean_text = self.clean_text_for_speech(text)
        logger.info(f"🎙️ OPTIMIZED TEXT: '{clean_text}'")
        
        if not clean_text.strip():
            logger.warning("No valid text to synthesize after cleaning")
            return None
        
        # Prevent processing if text is too long (causes chunking issues)
        if len(clean_text) > 500:
            logger.warning(f"Text too long ({len(clean_text)} chars), truncating to prevent chunking")
            clean_text = clean_text[:500] + "."
        
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/text-to-speech/{self.voice_id}",
                        headers={
                            "Accept": "audio/mpeg",
                            "Content-Type": "application/json",
                            "xi-api-key": self.api_key
                        },
                        json={
                            "text": clean_text,
                            "model_id": self.model_id,
                            "voice_settings": self.voice_settings
                        },
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        self.last_request_time = time.time()
                        logger.info(f"🎙️ ELEVENLABS SUCCESS for: '{clean_text[:50]}...'")
                        return response.content
                    
                    elif response.status_code == 429:
                        # Rate limited - wait longer and retry
                        if attempt < retries - 1:
                            wait_time = 3 + (2 ** attempt)  # Longer exponential backoff
                            logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error("Rate limit exceeded after retries")
                            return None
                    
                    else:
                        logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                        if attempt < retries - 1:
                            await asyncio.sleep(1)
                            continue
                        else:
                            return None
                        
            except httpx.TimeoutException:
                if attempt < retries - 1:
                    logger.warning(f"Request timeout, retrying (attempt {attempt + 1}/{retries})")
                    await asyncio.sleep(2)
                    continue
                else:
                    logger.error("Request timeout after retries")
                    return None
            
            except Exception as e:
                if attempt < retries - 1:
                    logger.warning(f"Request failed, retrying (attempt {attempt + 1}/{retries}): {e}")
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.error(f"ElevenLabs audio generation failed: {e}")
                    return None
        
        return None

# Global service instance
voice_service = ElevenLabsVoiceService()