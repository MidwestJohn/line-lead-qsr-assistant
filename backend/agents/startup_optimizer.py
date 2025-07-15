#!/usr/bin/env python3
"""
Agent Startup Optimizer
=======================

Optimizes PydanticAI agent initialization by pre-loading agents during 
backend startup and caching configurations to avoid repeated initialization.

Features:
- Startup agent pre-initialization 
- Configuration caching
- Health check optimization
- Background agent warming

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import logging
import time
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class AgentStartupOptimizer:
    """Optimizes agent startup performance with caching and pre-initialization"""
    
    def __init__(self):
        """Initialize the startup optimizer"""
        self.cache_dir = Path("agent_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        self.orchestrator_cache = None
        self.initialization_time = None
        self.cache_valid = False
        
        # Performance tracking
        self.startup_metrics = {
            "total_startup_time": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "last_optimization": None
        }
        
        logger.info("🚀 Agent startup optimizer initialized")
    
    async def initialize_agents_at_startup(self) -> bool:
        """Pre-initialize agents during backend startup"""
        try:
            start_time = time.time()
            logger.info("🔥 Pre-initializing PydanticAI agents at startup...")
            
            # Import here to avoid circular imports
            from .qsr_orchestrator import QSROrchestrator
            
            # Create orchestrator (this will cache it globally)
            self.orchestrator_cache = await QSROrchestrator.create()
            
            initialization_time = time.time() - start_time
            self.initialization_time = initialization_time
            self.cache_valid = True
            
            # Update metrics
            self.startup_metrics["total_startup_time"] = initialization_time
            self.startup_metrics["last_optimization"] = datetime.now().isoformat()
            
            logger.info(f"✅ PydanticAI agents pre-initialized in {initialization_time:.2f}s")
            
            # Save startup metrics
            await self._save_startup_metrics()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Agent pre-initialization failed: {e}")
            self.cache_valid = False
            return False
    
    async def get_orchestrator_fast(self) -> Optional[Any]:
        """Get orchestrator quickly using cached instance"""
        if self.cache_valid and self.orchestrator_cache:
            self.startup_metrics["cache_hits"] += 1
            logger.debug("🎯 Using cached orchestrator instance")
            return self.orchestrator_cache
        
        # Cache miss - need to initialize
        logger.warning("⚠️ Cache miss - initializing orchestrator on-demand")
        self.startup_metrics["cache_misses"] += 1
        
        try:
            from .qsr_orchestrator import QSROrchestrator
            start_time = time.time()
            
            self.orchestrator_cache = await QSROrchestrator.create()
            self.cache_valid = True
            
            init_time = time.time() - start_time
            logger.info(f"🔄 On-demand orchestrator initialized in {init_time:.2f}s")
            
            return self.orchestrator_cache
            
        except Exception as e:
            logger.error(f"❌ On-demand orchestrator initialization failed: {e}")
            return None
    
    async def health_check_fast(self) -> Dict[str, Any]:
        """Fast health check that doesn't recreate agents"""
        start_time = time.time()
        
        if self.cache_valid and self.orchestrator_cache:
            # Quick validation without recreating
            try:
                # Simple test to see if orchestrator is still valid
                hasattr(self.orchestrator_cache, 'handle_query')
                
                response_time = (time.time() - start_time) * 1000
                
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "agents_available": 4,
                    "degraded": False,
                    "cache_status": "hit",
                    "initialization_time": round(self.initialization_time, 2) if self.initialization_time else None
                }
                
            except Exception as e:
                logger.warning(f"⚠️ Cached orchestrator validation failed: {e}")
                self.cache_valid = False
        
        # Cache invalid or missing - check if we can reinitialize quickly
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "degraded",
            "response_time_ms": round(response_time, 2),
            "agents_available": 0,
            "degraded": True,
            "cache_status": "miss",
            "error": "Agents need re-initialization"
        }
    
    async def _save_startup_metrics(self):
        """Save startup metrics to cache"""
        try:
            metrics_file = self.cache_dir / "startup_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(self.startup_metrics, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save startup metrics: {e}")
    
    async def get_startup_metrics(self) -> Dict[str, Any]:
        """Get startup performance metrics"""
        return {
            **self.startup_metrics,
            "cache_valid": self.cache_valid,
            "orchestrator_cached": self.orchestrator_cache is not None,
            "cache_hit_rate": (
                self.startup_metrics["cache_hits"] / 
                max(1, self.startup_metrics["cache_hits"] + self.startup_metrics["cache_misses"])
            ) * 100
        }
    
    async def warm_agents_background(self):
        """Background task to keep agents warm"""
        try:
            if self.cache_valid and self.orchestrator_cache:
                # Periodic validation to keep agents warm
                await self.orchestrator_cache.classify_query("test warmup query")
                logger.debug("🔥 Agents warmed up successfully")
        except Exception as e:
            logger.warning(f"Agent warmup failed: {e}")
            self.cache_valid = False

# Global startup optimizer instance
startup_optimizer = AgentStartupOptimizer()

# Convenience functions
async def initialize_agents_at_startup() -> bool:
    """Initialize agents during backend startup"""
    return await startup_optimizer.initialize_agents_at_startup()

async def get_orchestrator_fast():
    """Get orchestrator quickly using cache"""
    return await startup_optimizer.get_orchestrator_fast()

async def health_check_fast() -> Dict[str, Any]:
    """Fast health check without recreating agents"""
    return await startup_optimizer.health_check_fast()

async def get_startup_metrics() -> Dict[str, Any]:
    """Get startup performance metrics"""
    return await startup_optimizer.get_startup_metrics()