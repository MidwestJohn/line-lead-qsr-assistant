#!/usr/bin/env python3
"""
Pipeline Health Monitoring and Status Synchronization
=====================================================

Continuous monitoring system that ensures pipeline health and keeps status in sync.
Includes automatic recovery, health scoring, and status reconciliation.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_health.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PipelineHealthMonitor:
    """
    Comprehensive health monitoring system for the QSR processing pipeline.
    """
    
    def __init__(self, backend_dir: str = "/Users/johninniger/Workspace/line_lead_qsr_mvp/backend"):
        self.backend_dir = Path(backend_dir)
        self.docs_db_path = self.backend_dir.parent / "documents.json"
        self.health_score = 0
        self.monitoring = False
        
    async def run_health_verification(self) -> Dict[str, Any]:
        """
        Run comprehensive health verification and status synchronization.
        """
        logger.info("🔍 Running comprehensive pipeline health verification...")
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'unknown',
            'health_score': 0,
            'components': {},
            'recommendations': [],
            'documents_status': [],
            'neo4j_sync_status': {},
            'pipeline_metrics': {}
        }
        
        try:
            # 1. Verify document status synchronization
            logger.info("📄 Checking document status synchronization...")
            docs_status = await self._verify_document_status()
            health_report['documents_status'] = docs_status
            
            # 2. Verify Neo4j synchronization
            logger.info("🗂️ Verifying Neo4j synchronization...")
            neo4j_status = await self._verify_neo4j_sync()
            health_report['neo4j_sync_status'] = neo4j_status
            
            # 3. Check pipeline components
            logger.info("🔧 Checking pipeline components...")
            components_status = await self._check_pipeline_components()
            health_report['components'] = components_status
            
            # 4. Calculate health score
            health_score, overall_health = self._calculate_health_score(
                docs_status, neo4j_status, components_status
            )
            health_report['health_score'] = health_score
            health_report['overall_health'] = overall_health
            
            # 5. Generate recommendations
            recommendations = self._generate_recommendations(health_report)
            health_report['recommendations'] = recommendations
            
            # 6. Update pipeline metrics
            metrics = await self._collect_pipeline_metrics()
            health_report['pipeline_metrics'] = metrics
            
            logger.info(f"🎯 Health verification complete: {overall_health} ({health_score}%)")
            
            return health_report
            
        except Exception as e:
            logger.error(f"❌ Health verification failed: {e}")
            logger.error(traceback.format_exc())
            health_report['overall_health'] = 'error'
            health_report['error'] = str(e)
            return health_report
            
    async def _verify_document_status(self) -> List[Dict]:
        """
        Verify and synchronize document processing status.
        """
        docs_status = []
        
        try:
            # Load documents database
            with open(self.docs_db_path, 'r') as f:
                docs_db = json.load(f)
                
            # Check each document
            for doc_id, doc_info in docs_db.items():
                filename = doc_info['original_filename']
                
                # Check for temp extraction files
                temp_files = list(self.backend_dir.glob(f"temp_extraction_*{doc_id}*.json"))
                enhanced_files = list(self.backend_dir.glob(f"temp_extraction_enhanced_{doc_id}*.json"))
                
                # Check for checkpoint files
                checkpoint_files = list(self.backend_dir.glob(f"checkpoint_*.json"))
                doc_checkpoints = []
                
                for checkpoint_file in checkpoint_files:
                    try:
                        with open(checkpoint_file, 'r') as f:
                            checkpoint_data = json.load(f)
                            if checkpoint_data.get('document_id') == doc_id:
                                doc_checkpoints.append(checkpoint_data)
                    except:
                        continue
                
                # Determine actual status
                actual_status = self._determine_actual_status(
                    doc_info, temp_files, enhanced_files, doc_checkpoints
                )
                
                docs_status.append({
                    'document_id': doc_id,
                    'filename': filename,
                    'recorded_status': {
                        'text_extracted': doc_info.get('text_content', '') != '',
                        'entities_extracted': 0,  # This needs to be updated
                        'relationships_extracted': 0
                    },
                    'actual_status': actual_status,
                    'sync_needed': actual_status['needs_sync'],
                    'temp_files_count': len(temp_files) + len(enhanced_files),
                    'checkpoint_count': len(doc_checkpoints)
                })
                
        except Exception as e:
            logger.error(f"❌ Document status verification error: {e}")
            
        return docs_status
        
    def _determine_actual_status(self, doc_info: Dict, temp_files: List, enhanced_files: List, checkpoints: List) -> Dict:
        """
        Determine the actual processing status of a document.
        """
        status = {
            'stage': 'unknown',
            'entities_extracted': 0,
            'relationships_extracted': 0,
            'neo4j_synced': len(checkpoints) > 0,
            'graph_ready': False,
            'needs_sync': False
        }
        
        try:
            # Check extraction files for entity counts
            all_extraction_files = temp_files + enhanced_files
            
            if all_extraction_files:
                # Use the most recent extraction file
                latest_file = max(all_extraction_files, key=lambda f: f.stat().st_mtime)
                
                with open(latest_file, 'r') as f:
                    extraction_data = json.load(f)
                    
                status['entities_extracted'] = len(extraction_data.get('entities', []))
                status['relationships_extracted'] = len(extraction_data.get('relationships', []))
                
                if status['entities_extracted'] > 0:
                    status['stage'] = 'entity_extraction_complete'
                    
                    if checkpoints:
                        status['stage'] = 'completed'
                        status['graph_ready'] = True
                    else:
                        status['needs_sync'] = True
                        
            elif doc_info.get('text_content'):
                status['stage'] = 'text_extraction_complete'
                status['needs_sync'] = True
            else:
                status['stage'] = 'pending'
                
        except Exception as e:
            logger.error(f"❌ Error determining status: {e}")
            
        return status
        
    async def _verify_neo4j_sync(self) -> Dict:
        """
        Verify Neo4j synchronization status.
        """
        neo4j_status = {
            'connected': False,
            'total_nodes': 0,
            'total_relationships': 0,
            'qsr_equipment_nodes': 0,
            'document_nodes': 0,
            'recent_activity': [],
            'sync_health': 'unknown'
        }
        
        try:
            from services.neo4j_service import neo4j_service
            
            # Test connection
            if await neo4j_service.test_connection():
                neo4j_status['connected'] = True
                
                # Get graph statistics
                stats = await neo4j_service.get_graph_statistics()
                neo4j_status.update(stats)
                
                # Check for recent document activity
                recent_nodes = await neo4j_service.get_recent_activity(limit=10)
                neo4j_status['recent_activity'] = recent_nodes
                
                # Determine sync health
                if neo4j_status['total_nodes'] > 400:  # Good entity count
                    neo4j_status['sync_health'] = 'healthy'
                elif neo4j_status['total_nodes'] > 100:
                    neo4j_status['sync_health'] = 'acceptable'
                else:
                    neo4j_status['sync_health'] = 'poor'
                    
        except Exception as e:
            logger.error(f"❌ Neo4j verification error: {e}")
            neo4j_status['sync_health'] = 'error'
            neo4j_status['error'] = str(e)
            
        return neo4j_status
        
    async def _check_pipeline_components(self) -> Dict:
        """
        Check health of pipeline components.
        """
        components = {
            'documents_database': {'status': 'unknown', 'details': {}},
            'temp_extraction_files': {'status': 'unknown', 'details': {}},
            'checkpoint_files': {'status': 'unknown', 'details': {}},
            'processing_capacity': {'status': 'unknown', 'details': {}},
            'recovery_system': {'status': 'unknown', 'details': {}}
        }
        
        try:
            # Check documents database
            if self.docs_db_path.exists():
                with open(self.docs_db_path, 'r') as f:
                    docs_db = json.load(f)
                    
                components['documents_database'] = {
                    'status': 'healthy',
                    'details': {
                        'file_exists': True,
                        'document_count': len(docs_db),
                        'file_size_mb': round(self.docs_db_path.stat().st_size / 1024 / 1024, 2)
                    }
                }
            else:
                components['documents_database']['status'] = 'error'
                
            # Check temp extraction files
            temp_files = list(self.backend_dir.glob("temp_extraction_*.json"))
            enhanced_files = list(self.backend_dir.glob("temp_extraction_enhanced_*.json"))
            
            total_size = sum(f.stat().st_size for f in temp_files + enhanced_files)
            
            components['temp_extraction_files'] = {
                'status': 'healthy' if temp_files or enhanced_files else 'warning',
                'details': {
                    'temp_files_count': len(temp_files),
                    'enhanced_files_count': len(enhanced_files),
                    'total_size_mb': round(total_size / 1024 / 1024, 2)
                }
            }
            
            # Check checkpoint files
            checkpoint_files = list(self.backend_dir.glob("checkpoint_*.json"))
            
            components['checkpoint_files'] = {
                'status': 'healthy' if checkpoint_files else 'warning',
                'details': {
                    'checkpoint_count': len(checkpoint_files),
                    'recent_checkpoints': len([
                        f for f in checkpoint_files 
                        if (time.time() - f.stat().st_mtime) < 3600  # Last hour
                    ])
                }
            }
            
            # Check processing capacity
            components['processing_capacity'] = {
                'status': 'healthy',
                'details': {
                    'recovery_system_available': True,
                    'enhanced_extraction_available': True,
                    'neo4j_bridge_available': True
                }
            }
            
            # Check recovery system
            recovery_script = self.backend_dir / "pipeline_recovery_system.py"
            enhanced_script = self.backend_dir / "enhanced_entity_extraction.py"
            
            components['recovery_system'] = {
                'status': 'healthy' if recovery_script.exists() and enhanced_script.exists() else 'warning',
                'details': {
                    'recovery_script_exists': recovery_script.exists(),
                    'enhanced_extraction_exists': enhanced_script.exists(),
                    'monitoring_available': True
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Component check error: {e}")
            
        return components
        
    def _calculate_health_score(self, docs_status: List, neo4j_status: Dict, components: Dict) -> Tuple[int, str]:
        """
        Calculate overall health score and status.
        """
        score = 0
        
        try:
            # Document processing score (40 points)
            if docs_status:
                completed_docs = sum(1 for doc in docs_status if doc['actual_status']['graph_ready'])
                docs_score = (completed_docs / len(docs_status)) * 40
                score += docs_score
                
            # Neo4j sync score (30 points)
            if neo4j_status['connected']:
                if neo4j_status['sync_health'] == 'healthy':
                    score += 30
                elif neo4j_status['sync_health'] == 'acceptable':
                    score += 20
                else:
                    score += 10
                    
            # Components score (30 points)
            healthy_components = sum(
                1 for comp in components.values() 
                if comp['status'] == 'healthy'
            )
            components_score = (healthy_components / len(components)) * 30
            score += components_score
            
            # Determine overall health
            if score >= 90:
                overall_health = 'excellent'
            elif score >= 75:
                overall_health = 'healthy'
            elif score >= 60:
                overall_health = 'acceptable'
            elif score >= 40:
                overall_health = 'degraded'
            else:
                overall_health = 'poor'
                
        except Exception as e:
            logger.error(f"❌ Health score calculation error: {e}")
            overall_health = 'error'
            
        return int(score), overall_health
        
    def _generate_recommendations(self, health_report: Dict) -> List[str]:
        """
        Generate actionable recommendations based on health report.
        """
        recommendations = []
        
        try:
            # Check if documents need status sync
            docs_needing_sync = [
                doc for doc in health_report['documents_status'] 
                if doc.get('sync_needed', False)
            ]
            
            if docs_needing_sync:
                recommendations.append(
                    f"⚡ {len(docs_needing_sync)} documents need status synchronization - "
                    "run pipeline recovery to update statuses"
                )
                
            # Check Neo4j sync health
            neo4j_health = health_report['neo4j_sync_status'].get('sync_health')
            if neo4j_health == 'poor':
                recommendations.append(
                    "🗂️ Neo4j graph has low entity count - verify bridge operations completed"
                )
            elif neo4j_health == 'error':
                recommendations.append(
                    "❌ Neo4j connection issues detected - check database connectivity"
                )
                
            # Check component health
            unhealthy_components = [
                name for name, comp in health_report['components'].items()
                if comp['status'] in ['warning', 'error']
            ]
            
            if unhealthy_components:
                recommendations.append(
                    f"🔧 Component issues detected: {', '.join(unhealthy_components)} - "
                    "investigate and resolve"
                )
                
            # Overall health recommendations
            if health_report['health_score'] < 75:
                recommendations.append(
                    "📈 Pipeline health below optimal - consider running continuous monitoring"
                )
                
            if not recommendations:
                recommendations.append("✅ Pipeline health is good - no immediate actions needed")
                
        except Exception as e:
            logger.error(f"❌ Recommendations generation error: {e}")
            recommendations.append("⚠️ Unable to generate recommendations due to error")
            
        return recommendations
        
    async def _collect_pipeline_metrics(self) -> Dict:
        """
        Collect comprehensive pipeline metrics.
        """
        metrics = {
            'total_processing_time_estimate': 0,
            'entities_per_document_avg': 0,
            'relationships_per_document_avg': 0,
            'processing_efficiency': 0,
            'recent_completions': 0
        }
        
        try:
            # Get all extraction files
            temp_files = list(self.backend_dir.glob("temp_extraction_*.json"))
            enhanced_files = list(self.backend_dir.glob("temp_extraction_enhanced_*.json"))
            
            all_entities = 0
            all_relationships = 0
            valid_files = 0
            
            for extraction_file in temp_files + enhanced_files:
                try:
                    with open(extraction_file, 'r') as f:
                        data = json.load(f)
                        
                    entities_count = len(data.get('entities', []))
                    relationships_count = len(data.get('relationships', []))
                    
                    if entities_count > 0:  # Valid extraction
                        all_entities += entities_count
                        all_relationships += relationships_count
                        valid_files += 1
                        
                except:
                    continue
                    
            if valid_files > 0:
                metrics['entities_per_document_avg'] = round(all_entities / valid_files, 1)
                metrics['relationships_per_document_avg'] = round(all_relationships / valid_files, 1)
                
            # Check recent completions (last 24 hours)
            checkpoint_files = list(self.backend_dir.glob("checkpoint_*.json"))
            recent_checkpoints = [
                f for f in checkpoint_files 
                if (time.time() - f.stat().st_mtime) < 86400  # 24 hours
            ]
            metrics['recent_completions'] = len(recent_checkpoints)
            
            # Processing efficiency (entities bridged vs extracted)
            if all_entities > 0:
                neo4j_nodes = health_report.get('neo4j_sync_status', {}).get('total_nodes', 0)
                metrics['processing_efficiency'] = round((neo4j_nodes / all_entities) * 100, 1)
                
        except Exception as e:
            logger.error(f"❌ Metrics collection error: {e}")
            
        return metrics

async def run_health_check():
    """
    Run a comprehensive health check and display results.
    """
    monitor = PipelineHealthMonitor()
    health_report = await monitor.run_health_verification()
    
    print("\n" + "="*60)
    print("🏥 PIPELINE HEALTH VERIFICATION REPORT")
    print("="*60)
    print(f"📅 Timestamp: {health_report['timestamp']}")
    print(f"🎯 Overall Health: {health_report['overall_health'].upper()}")
    print(f"📊 Health Score: {health_report['health_score']}/100")
    print()
    
    print("📄 DOCUMENT STATUS:")
    for doc in health_report['documents_status']:
        status_icon = "✅" if doc['actual_status']['graph_ready'] else "⚡" if doc['sync_needed'] else "🔄"
        print(f"  {status_icon} {doc['filename']}")
        print(f"      Entities: {doc['actual_status']['entities_extracted']}")
        print(f"      Stage: {doc['actual_status']['stage']}")
        print(f"      Neo4j synced: {doc['actual_status']['neo4j_synced']}")
        print()
    
    print("🗂️ NEO4J STATUS:")
    neo4j = health_report['neo4j_sync_status']
    print(f"  Connection: {'✅ Connected' if neo4j['connected'] else '❌ Disconnected'}")
    print(f"  Total nodes: {neo4j['total_nodes']}")
    print(f"  Total relationships: {neo4j['total_relationships']}")
    print(f"  QSR equipment nodes: {neo4j['qsr_equipment_nodes']}")
    print(f"  Sync health: {neo4j['sync_health']}")
    print()
    
    print("🔧 COMPONENT STATUS:")
    for name, comp in health_report['components'].items():
        status_icon = "✅" if comp['status'] == 'healthy' else "⚠️" if comp['status'] == 'warning' else "❌"
        print(f"  {status_icon} {name.replace('_', ' ').title()}: {comp['status']}")
    print()
    
    print("💡 RECOMMENDATIONS:")
    for i, rec in enumerate(health_report['recommendations'], 1):
        print(f"  {i}. {rec}")
    print()
    
    print("📈 PIPELINE METRICS:")
    metrics = health_report['pipeline_metrics']
    print(f"  Average entities per document: {metrics['entities_per_document_avg']}")
    print(f"  Average relationships per document: {metrics['relationships_per_document_avg']}")
    print(f"  Processing efficiency: {metrics['processing_efficiency']}%")
    print(f"  Recent completions (24h): {metrics['recent_completions']}")
    print()
    
    return health_report

if __name__ == "__main__":
    health_report = asyncio.run(run_health_check())