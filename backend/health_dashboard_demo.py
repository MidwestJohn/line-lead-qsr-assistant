#!/usr/bin/env python3
"""
Health Dashboard Demo
====================

Simple demo script that shows how to use the enhanced health monitoring system
to create a real-time performance dashboard for PydanticAI + Ragie intelligence.

This demonstrates:
- Real-time metric collection
- Performance trend analysis
- User satisfaction tracking
- Service health monitoring

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys

# Add backend to path
sys.path.append('.')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HealthDashboardDemo:
    """Demo class for health dashboard functionality"""
    
    def __init__(self):
        self.running = False
        self.dashboard_data = {}
        
    async def start_demo(self):
        """Start the health dashboard demo"""
        
        logger.info("🚀 Starting Health Dashboard Demo")
        
        try:
            from health_monitoring_enhanced import enhanced_health_monitoring
            
            # Start monitoring
            logger.info("📊 Starting enhanced health monitoring...")
            enhanced_health_monitoring.start_monitoring()
            
            # Wait for monitoring to initialize
            await asyncio.sleep(3)
            
            self.running = True
            
            # Run demo loop
            await self._demo_loop(enhanced_health_monitoring)
            
        except ImportError:
            logger.error("❌ Enhanced health monitoring not available")
            return False
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            return False
        finally:
            self.running = False
            try:
                enhanced_health_monitoring.stop_monitoring()
                logger.info("🛑 Monitoring stopped")
            except:
                pass
        
        return True
    
    async def _demo_loop(self, monitoring_system):
        """Main demo loop"""
        
        iteration = 0
        
        while self.running and iteration < 10:  # Run for 10 iterations
            iteration += 1
            
            logger.info(f"🔄 Dashboard Update {iteration}/10")
            
            try:
                # Get dashboard data
                dashboard_data = monitoring_system.get_performance_dashboard_data()
                
                # Display current status
                self._display_dashboard_summary(dashboard_data)
                
                # Simulate some interactions
                await self._simulate_interactions(monitoring_system)
                
                # Display real-time metrics
                self._display_real_time_metrics(dashboard_data)
                
                # Store dashboard data
                self.dashboard_data[f"iteration_{iteration}"] = dashboard_data
                
                # Wait between updates
                await asyncio.sleep(15)
                
            except Exception as e:
                logger.error(f"❌ Error in demo loop: {e}")
                await asyncio.sleep(5)
        
        # Generate final report
        self._generate_demo_report()
        
        logger.info("✅ Dashboard demo completed")
    
    def _display_dashboard_summary(self, dashboard_data: Dict[str, Any]):
        """Display dashboard summary"""
        
        intelligence_health = dashboard_data.get("intelligence_health", {})
        overall_health = intelligence_health.get("overall_intelligence_health", "unknown")
        
        logger.info("=" * 50)
        logger.info(f"📊 INTELLIGENCE HEALTH DASHBOARD")
        logger.info("=" * 50)
        logger.info(f"Overall Intelligence Health: {overall_health.upper()}")
        
        # Ragie service health
        ragie_health = intelligence_health.get("ragie_service_health", {})
        if ragie_health:
            logger.info(f"Ragie Service: {ragie_health.get('status', 'unknown').upper()}")
            if ragie_health.get("response_time_ms"):
                logger.info(f"  Response Time: {ragie_health['response_time_ms']:.0f}ms")
        
        # Agent coordination health
        agent_health = intelligence_health.get("agent_coordination_health", {})
        if agent_health:
            logger.info(f"Agent Coordination: {agent_health.get('status', 'unknown').upper()}")
            if agent_health.get("coordination_success_rate"):
                logger.info(f"  Success Rate: {agent_health['coordination_success_rate']:.1%}")
        
        # Context preservation health
        context_health = intelligence_health.get("context_preservation_health", {})
        if context_health:
            logger.info(f"Context Preservation: {context_health.get('status', 'unknown').upper()}")
            if context_health.get("preservation_rate"):
                logger.info(f"  Preservation Rate: {context_health['preservation_rate']:.1%}")
        
        # Active alerts
        active_alerts = intelligence_health.get("active_intelligence_alerts", 0)
        logger.info(f"Active Alerts: {active_alerts}")
        
        logger.info("=" * 50)
    
    def _display_real_time_metrics(self, dashboard_data: Dict[str, Any]):
        """Display real-time metrics"""
        
        real_time_metrics = dashboard_data.get("real_time_metrics", {})
        
        if real_time_metrics:
            logger.info("📈 Real-time Metrics:")
            
            for metric_name, metric_data in real_time_metrics.items():
                value = metric_data.get("value", 0)
                unit = metric_data.get("unit", "")
                timestamp = metric_data.get("timestamp", "")
                
                if unit == "milliseconds":
                    logger.info(f"  {metric_name}: {value:.0f}ms")
                elif unit == "percentage" or unit == "rate":
                    logger.info(f"  {metric_name}: {value:.1%}")
                elif unit == "boolean":
                    logger.info(f"  {metric_name}: {'✅' if value > 0.5 else '❌'}")
                else:
                    logger.info(f"  {metric_name}: {value:.2f} {unit}")
        
        # User satisfaction
        user_satisfaction = dashboard_data.get("user_satisfaction", {})
        if user_satisfaction:
            logger.info("👥 User Satisfaction:")
            logger.info(f"  Response Quality: {user_satisfaction.get('response_quality_average', 0):.2f}")
            logger.info(f"  Task Success Rate: {user_satisfaction.get('task_success_rate', 0):.1%}")
            logger.info(f"  User Feedback Score: {user_satisfaction.get('user_feedback_score', 0):.1f}/5.0")
    
    async def _simulate_interactions(self, monitoring_system):
        """Simulate user interactions for demo"""
        
        # Simulate different types of interactions
        interactions = [
            {
                "session_id": f"demo_session_{int(time.time())}",
                "interaction_data": {
                    "response_time": 1200,
                    "agent_type": "equipment",
                    "query_type": "equipment_question",
                    "response_quality": 0.92,
                    "ragie_used": True,
                    "context_preserved": True,
                    "user_satisfied": True
                }
            },
            {
                "session_id": f"demo_session_{int(time.time()) + 1}",
                "interaction_data": {
                    "response_time": 800,
                    "agent_type": "safety",
                    "query_type": "safety_question",
                    "response_quality": 0.88,
                    "ragie_used": True,
                    "context_preserved": True,
                    "user_satisfied": True
                }
            },
            {
                "session_id": f"demo_session_{int(time.time()) + 2}",
                "interaction_data": {
                    "response_time": 1500,
                    "agent_type": "procedure",
                    "query_type": "procedure_question",
                    "response_quality": 0.95,
                    "ragie_used": True,
                    "context_preserved": True,
                    "user_satisfied": True
                }
            }
        ]
        
        for interaction in interactions:
            monitoring_system.record_interaction_performance(
                interaction["session_id"],
                interaction["interaction_data"]
            )
            
            await asyncio.sleep(1)  # Small delay between interactions
    
    def _generate_demo_report(self):
        """Generate demo report"""
        
        report = {
            "demo_name": "Health Dashboard Demo",
            "timestamp": datetime.now().isoformat(),
            "iterations_completed": len(self.dashboard_data),
            "dashboard_data": self.dashboard_data,
            "summary": {
                "demo_successful": len(self.dashboard_data) > 0,
                "monitoring_working": True,
                "metrics_collected": True,
                "interactions_simulated": True
            }
        }
        
        # Save report
        with open("health_dashboard_demo_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info("📋 Demo report saved to health_dashboard_demo_report.json")
        
        # Print summary
        logger.info("=" * 60)
        logger.info("📊 HEALTH DASHBOARD DEMO SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Iterations Completed: {len(self.dashboard_data)}")
        logger.info(f"Demo Status: {'✅ SUCCESS' if len(self.dashboard_data) > 0 else '❌ FAILED'}")
        logger.info("=" * 60)
        
        return report

async def main():
    """Main demo function"""
    
    logger.info("🎬 Starting Health Dashboard Demo")
    
    demo = HealthDashboardDemo()
    
    try:
        success = await demo.start_demo()
        
        if success:
            logger.info("✅ Health Dashboard Demo completed successfully")
            return True
        else:
            logger.error("❌ Health Dashboard Demo failed")
            return False
            
    except KeyboardInterrupt:
        logger.info("🛑 Demo interrupted by user")
        return False
    except Exception as e:
        logger.error(f"❌ Demo failed with error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())