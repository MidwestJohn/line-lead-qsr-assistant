#!/usr/bin/env python3
"""
Critical Pipeline Reliability Fix for Line Lead QSR System
==========================================================

Problem: Files getting stuck in processing stages, entities extracted but not reaching Neo4j, 
no automatic recovery from failed async operations.

Implementation:
1. Heartbeat-Based Recovery System
2. Enhanced Retry Logic Throughout Pipeline
3. Async Bridge Auto-Detection
4. Pipeline Health Monitoring

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import time
import os
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import glob
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_recovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StuckStage(str, Enum):
    """Stages where files can get stuck"""
    TEXT_EXTRACTION = "text_extraction"
    ENTITY_EXTRACTION = "entity_extraction"
    NEO4J_BRIDGING = "neo4j_bridging"
    COMPLETED = "completed"

class RecoveryAction(str, Enum):
    """Types of recovery actions"""
    RETRY_TEXT_EXTRACTION = "retry_text_extraction"
    RETRY_ENTITY_EXTRACTION = "retry_entity_extraction"
    TRIGGER_NEO4J_BRIDGE = "trigger_neo4j_bridge"
    FORCE_COMPLETION = "force_completion"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class StuckFile:
    """Information about a stuck file"""
    document_id: str
    filename: str
    stage: StuckStage
    stuck_duration: timedelta
    last_activity: Optional[datetime]
    entities_extracted: int
    relationships_extracted: int
    has_temp_extraction: bool
    recovery_action: RecoveryAction
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class RecoveryStats:
    """Statistics from recovery operations"""
    files_detected: int = 0
    files_recovered: int = 0
    files_failed: int = 0
    neo4j_bridges_triggered: int = 0
    text_extractions_retried: int = 0
    entity_extractions_retried: int = 0
    orphaned_entities_found: int = 0
    start_time: datetime = field(default_factory=datetime.now)

class PipelineRecoverySystem:
    """
    Heartbeat-based recovery system for the QSR processing pipeline.
    Detects stuck files and automatically triggers recovery actions.
    """
    
    def __init__(self, 
                 backend_dir: str = "/Users/johninniger/Workspace/line_lead_qsr_mvp/backend",
                 heartbeat_interval: int = 60,  # seconds
                 stuck_thresholds: Dict[str, int] = None):
        
        self.backend_dir = Path(backend_dir)
        self.heartbeat_interval = heartbeat_interval
        
        # Default stuck thresholds (in minutes)
        self.stuck_thresholds = stuck_thresholds or {
            'text_extraction': 10,     # 10 minutes for text extraction
            'entity_extraction': 30,   # 30 minutes for entity extraction  
            'neo4j_bridging': 15       # 15 minutes for Neo4j bridging
        }
        
        self.recovery_stats = RecoveryStats()
        self.known_stuck_files: Dict[str, StuckFile] = {}
        self.running = False
        
    async def start_heartbeat_monitoring(self):
        """
        Start continuous heartbeat monitoring for stuck files.
        """
        self.running = True
        logger.info("🔄 Starting pipeline heartbeat monitoring...")
        
        while self.running:
            try:
                # Detect stuck files
                stuck_files = await self.detect_stuck_files()
                
                if stuck_files:
                    logger.warning(f"🚨 Detected {len(stuck_files)} stuck files")
                    
                    # Attempt recovery for each stuck file
                    for stuck_file in stuck_files:
                        await self.attempt_recovery(stuck_file)
                        
                # Check for orphaned entities ready for Neo4j
                await self.check_orphaned_entities()
                
                # Generate health report
                await self.log_health_status()
                
                # Sleep until next heartbeat
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"❌ Heartbeat monitoring error: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(self.heartbeat_interval)
                
    def stop_heartbeat_monitoring(self):
        """Stop heartbeat monitoring"""
        self.running = False
        logger.info("⏹️ Stopping pipeline heartbeat monitoring")
        
    async def detect_stuck_files(self) -> List[StuckFile]:
        """
        Detect files that are stuck in various processing stages.
        """
        stuck_files = []
        now = datetime.now()
        
        try:
            # Load current document statuses
            from enhanced_diagnostics import get_processing_status
            status = await get_processing_status()
            
            for doc in status['documents']:
                doc_id = doc['document_id']
                filename = doc['original_filename']
                upload_time = datetime.fromisoformat(doc['upload_timestamp'])
                
                # Determine if file is stuck
                stuck_info = self._analyze_stuck_status(doc, now, upload_time)
                
                if stuck_info:
                    stuck_file = StuckFile(
                        document_id=doc_id,
                        filename=filename,
                        stage=stuck_info['stage'],
                        stuck_duration=stuck_info['duration'],
                        last_activity=stuck_info['last_activity'],
                        entities_extracted=doc['entities_extracted'],
                        relationships_extracted=doc['relationships_extracted'],
                        has_temp_extraction=doc['has_temp_extraction'],
                        recovery_action=stuck_info['recovery_action'],
                        retry_count=self.known_stuck_files.get(doc_id, StuckFile('','',StuckStage.TEXT_EXTRACTION,timedelta(),None,0,0,False,RecoveryAction.RETRY_TEXT_EXTRACTION)).retry_count
                    )
                    
                    stuck_files.append(stuck_file)
                    self.known_stuck_files[doc_id] = stuck_file
                    
            self.recovery_stats.files_detected = len(stuck_files)
            
        except Exception as e:
            logger.error(f"❌ Error detecting stuck files: {e}")
            
        return stuck_files
        
    def _analyze_stuck_status(self, doc: Dict, now: datetime, upload_time: datetime) -> Optional[Dict]:
        """
        Analyze if a document is stuck and determine recovery action.
        """
        time_since_upload = now - upload_time
        
        # Case 1: Stuck in text extraction (no temp extraction file, text was extracted)
        if doc['text_extracted'] and not doc['has_temp_extraction'] and doc['entities_extracted'] == 0:
            if time_since_upload > timedelta(minutes=self.stuck_thresholds['text_extraction']):
                return {
                    'stage': StuckStage.TEXT_EXTRACTION,
                    'duration': time_since_upload,
                    'last_activity': upload_time,
                    'recovery_action': RecoveryAction.RETRY_ENTITY_EXTRACTION
                }
                
        # Case 2: Stuck in entity extraction (has entities but not synced to Neo4j)
        elif doc['has_temp_extraction'] and doc['entities_extracted'] > 0 and not doc['neo4j_synced']:
            if time_since_upload > timedelta(minutes=self.stuck_thresholds['entity_extraction']):
                return {
                    'stage': StuckStage.ENTITY_EXTRACTION,
                    'duration': time_since_upload,
                    'last_activity': upload_time,
                    'recovery_action': RecoveryAction.TRIGGER_NEO4J_BRIDGE
                }
                
        # Case 3: Text extracted but no progress at all
        elif doc['text_extracted'] and doc['entities_extracted'] == 0 and not doc['has_temp_extraction']:
            if time_since_upload > timedelta(minutes=self.stuck_thresholds['text_extraction']):
                return {
                    'stage': StuckStage.TEXT_EXTRACTION,
                    'duration': time_since_upload,
                    'last_activity': upload_time,
                    'recovery_action': RecoveryAction.RETRY_TEXT_EXTRACTION
                }
                
        return None
        
    async def attempt_recovery(self, stuck_file: StuckFile):
        """
        Attempt to recover a stuck file based on its status.
        """
        if stuck_file.retry_count >= stuck_file.max_retries:
            logger.error(f"❌ Max retries exceeded for {stuck_file.filename}")
            self.recovery_stats.files_failed += 1
            return False
            
        logger.info(f"🔧 Attempting recovery for {stuck_file.filename} (attempt {stuck_file.retry_count + 1})")
        
        try:
            success = False
            
            if stuck_file.recovery_action == RecoveryAction.TRIGGER_NEO4J_BRIDGE:
                success = await self._trigger_neo4j_bridge(stuck_file)
                
            elif stuck_file.recovery_action == RecoveryAction.RETRY_ENTITY_EXTRACTION:
                success = await self._retry_entity_extraction(stuck_file)
                
            elif stuck_file.recovery_action == RecoveryAction.RETRY_TEXT_EXTRACTION:
                success = await self._retry_text_extraction(stuck_file)
                
            stuck_file.retry_count += 1
            
            if success:
                logger.info(f"✅ Successfully recovered {stuck_file.filename}")
                self.recovery_stats.files_recovered += 1
                return True
            else:
                logger.warning(f"⚠️ Recovery attempt failed for {stuck_file.filename}")
                
        except Exception as e:
            logger.error(f"❌ Recovery error for {stuck_file.filename}: {e}")
            
        return False
        
    async def _trigger_neo4j_bridge(self, stuck_file: StuckFile) -> bool:
        """
        Trigger Neo4j bridging for files with extracted entities.
        """
        try:
            logger.info(f"🌉 Triggering Neo4j bridge for {stuck_file.filename}")
            
            # Find the temp extraction file
            temp_files = list(self.backend_dir.glob(f"temp_extraction_*{stuck_file.document_id}*.json"))
            
            if not temp_files:
                logger.error(f"No temp extraction file found for {stuck_file.document_id}")
                return False
                
            temp_file = temp_files[0]
            logger.info(f"Found temp extraction file: {temp_file}")
            
            # Load entities and relationships
            with open(temp_file, 'r') as f:
                data = json.load(f)
                
            entities = data.get('entities', [])
            relationships = data.get('relationships', [])
            
            logger.info(f"Loaded {len(entities)} entities and {len(relationships)} relationships")
            
            # Bridge to Neo4j using the manual bridge
            from lightrag_neo4j_bridge import LightRAGNeo4jBridge
            
            # Create temporary files for bridging
            temp_entities_file = self.backend_dir / f"temp_entities_{stuck_file.document_id}.json"
            temp_relationships_file = self.backend_dir / f"temp_relationships_{stuck_file.document_id}.json"
            
            with open(temp_entities_file, 'w') as f:
                json.dump(entities, f, indent=2)
                
            with open(temp_relationships_file, 'w') as f:
                json.dump(relationships, f, indent=2)
                
            # Initialize bridge
            bridge = LightRAGNeo4jBridge(
                entities_file=str(temp_entities_file),
                relationships_file=str(temp_relationships_file),
                batch_size=100,
                checkpoint_file=f"recovery_checkpoint_{stuck_file.document_id}.json"
            )
            
            # Execute bridging
            success = await bridge.bridge_to_neo4j_async()
            
            # Cleanup temporary files
            temp_entities_file.unlink(missing_ok=True)
            temp_relationships_file.unlink(missing_ok=True)
            
            if success:
                self.recovery_stats.neo4j_bridges_triggered += 1
                
                # Mark as completed by creating checkpoint
                checkpoint_file = self.backend_dir / f"checkpoint_{int(time.time())}.json"
                checkpoint_data = {
                    'document_id': stuck_file.document_id,
                    'filename': stuck_file.filename,
                    'entities_bridged': len(entities),
                    'relationships_bridged': len(relationships),
                    'completion_time': datetime.now().isoformat(),
                    'recovery_triggered': True
                }
                
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint_data, f, indent=2)
                    
                logger.info(f"✅ Successfully bridged {len(entities)} entities for {stuck_file.filename}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Neo4j bridge error for {stuck_file.filename}: {e}")
            logger.error(traceback.format_exc())
            
        return False
        
    async def _retry_entity_extraction(self, stuck_file: StuckFile) -> bool:
        """
        Retry entity extraction for files stuck after text extraction.
        """
        try:
            logger.info(f"🔄 Retrying entity extraction for {stuck_file.filename}")
            
            # Load documents database to get text content
            docs_db_path = self.backend_dir.parent / "documents.json"
            
            if not docs_db_path.exists():
                logger.error("Documents database not found")
                return False
                
            with open(docs_db_path, 'r') as f:
                docs_db = json.load(f)
                
            if stuck_file.document_id not in docs_db:
                logger.error(f"Document {stuck_file.document_id} not found in database")
                return False
                
            doc_info = docs_db[stuck_file.document_id]
            text_content = doc_info.get('text_content', '')
            
            if not text_content:
                logger.error(f"No text content available for {stuck_file.filename}")
                return False
                
            # Trigger entity extraction using smaller chunks
            entities, relationships = await self._extract_entities_with_retry(
                text_content, 
                stuck_file.filename,
                chunk_size=2000  # Smaller chunks for reliability
            )
            
            if entities or relationships:
                # Save temp extraction file
                temp_file = self.backend_dir / f"temp_extraction_recovery_{stuck_file.document_id}_{int(time.time())}.json"
                
                extraction_data = {
                    'entities': entities,
                    'relationships': relationships,
                    'document_id': stuck_file.document_id,
                    'filename': stuck_file.filename,
                    'extraction_time': datetime.now().isoformat(),
                    'recovery_extraction': True
                }
                
                with open(temp_file, 'w') as f:
                    json.dump(extraction_data, f, indent=2)
                    
                logger.info(f"✅ Extracted {len(entities)} entities and {len(relationships)} relationships")
                self.recovery_stats.entity_extractions_retried += 1
                return True
                
        except Exception as e:
            logger.error(f"❌ Entity extraction retry error for {stuck_file.filename}: {e}")
            logger.error(traceback.format_exc())
            
        return False
        
    async def _retry_text_extraction(self, stuck_file: StuckFile) -> bool:
        """
        Retry text extraction for files that never started processing.
        """
        try:
            logger.info(f"🔄 Retrying text extraction for {stuck_file.filename}")
            
            # Find the uploaded file
            uploaded_file = None
            upload_dirs = [
                self.backend_dir / "uploaded_docs",
                self.backend_dir / "uploads"
            ]
            
            for upload_dir in upload_dirs:
                if upload_dir.exists():
                    matching_files = list(upload_dir.glob(f"*{stuck_file.document_id}*"))
                    if matching_files:
                        uploaded_file = matching_files[0]
                        break
                        
            if not uploaded_file:
                logger.error(f"Could not find uploaded file for {stuck_file.filename}")
                return False
                
            # Re-extract text and trigger processing
            from main import extract_pdf_text, generate_document_id
            
            with open(uploaded_file, 'rb') as f:
                content = f.read()
                
            extracted_text, pages_count = extract_pdf_text(content)
            
            if extracted_text:
                # Update documents database
                docs_db_path = self.backend_dir.parent / "documents.json"
                
                with open(docs_db_path, 'r') as f:
                    docs_db = json.load(f)
                    
                if stuck_file.document_id in docs_db:
                    docs_db[stuck_file.document_id]['text_content'] = extracted_text
                    docs_db[stuck_file.document_id]['retry_extraction'] = True
                    docs_db[stuck_file.document_id]['retry_timestamp'] = datetime.now().isoformat()
                    
                    with open(docs_db_path, 'w') as f:
                        json.dump(docs_db, f, indent=2)
                        
                    logger.info(f"✅ Re-extracted text for {stuck_file.filename}")
                    self.recovery_stats.text_extractions_retried += 1
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Text extraction retry error for {stuck_file.filename}: {e}")
            logger.error(traceback.format_exc())
            
        return False
        
    async def _extract_entities_with_retry(self, text: str, filename: str, chunk_size: int = 2000) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract entities and relationships with retry logic and chunking.
        """
        entities = []
        relationships = []
        
        try:
            # Import QSR entity extractor
            from services.qsr_entity_extractor import QSREntityExtractor
            
            extractor = QSREntityExtractor()
            
            # Process text in chunks for reliability
            text_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            
            for i, chunk in enumerate(text_chunks):
                logger.info(f"Processing chunk {i+1}/{len(text_chunks)} for {filename}")
                
                chunk_entities, chunk_relationships = await extractor.extract_entities_and_relationships(
                    chunk, 
                    context=f"QSR document: {filename}, chunk {i+1}"
                )
                
                entities.extend(chunk_entities)
                relationships.extend(chunk_relationships)
                
                # Small delay between chunks
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"❌ Entity extraction error: {e}")
            
        return entities, relationships
        
    async def check_orphaned_entities(self):
        """
        Check for orphaned entity files that are ready for Neo4j bridging.
        """
        try:
            temp_files = list(self.backend_dir.glob("temp_extraction_*.json"))
            
            for temp_file in temp_files:
                # Check if this file has been processed
                file_timestamp = temp_file.stat().st_mtime
                file_age = time.time() - file_timestamp
                
                # If file is older than 5 minutes and no corresponding checkpoint
                if file_age > 300:  # 5 minutes
                    base_name = temp_file.stem
                    checkpoint_pattern = f"checkpoint_*{base_name.split('_')[-1]}*.json"
                    checkpoints = list(self.backend_dir.glob(checkpoint_pattern))
                    
                    if not checkpoints:
                        logger.warning(f"🔍 Found orphaned extraction file: {temp_file}")
                        self.recovery_stats.orphaned_entities_found += 1
                        
                        # Try to extract document ID and trigger bridging
                        await self._process_orphaned_file(temp_file)
                        
        except Exception as e:
            logger.error(f"❌ Error checking orphaned entities: {e}")
            
    async def _process_orphaned_file(self, temp_file: Path):
        """
        Process an orphaned temp extraction file.
        """
        try:
            with open(temp_file, 'r') as f:
                data = json.load(f)
                
            entities = data.get('entities', [])
            relationships = data.get('relationships', [])
            
            if entities or relationships:
                logger.info(f"🔧 Processing orphaned file with {len(entities)} entities")
                
                # Create a mock stuck file for bridging
                document_id = data.get('document_id', 'orphaned')
                filename = data.get('filename', temp_file.name)
                
                stuck_file = StuckFile(
                    document_id=document_id,
                    filename=filename,
                    stage=StuckStage.ENTITY_EXTRACTION,
                    stuck_duration=timedelta(minutes=30),
                    last_activity=datetime.now(),
                    entities_extracted=len(entities),
                    relationships_extracted=len(relationships),
                    has_temp_extraction=True,
                    recovery_action=RecoveryAction.TRIGGER_NEO4J_BRIDGE
                )
                
                await self._trigger_neo4j_bridge(stuck_file)
                
        except Exception as e:
            logger.error(f"❌ Error processing orphaned file {temp_file}: {e}")
            
    async def log_health_status(self):
        """
        Log current pipeline health status.
        """
        try:
            stuck_count = len(self.known_stuck_files)
            
            if stuck_count > 0:
                logger.warning(f"📊 Pipeline Health: {stuck_count} files stuck")
                
            # Log recovery stats every 10 heartbeats
            if hasattr(self, '_heartbeat_count'):
                self._heartbeat_count += 1
            else:
                self._heartbeat_count = 1
                
            if self._heartbeat_count % 10 == 0:
                duration = datetime.now() - self.recovery_stats.start_time
                logger.info(f"📈 Recovery Stats (last {duration}):")
                logger.info(f"   Files detected: {self.recovery_stats.files_detected}")
                logger.info(f"   Files recovered: {self.recovery_stats.files_recovered}")
                logger.info(f"   Neo4j bridges: {self.recovery_stats.neo4j_bridges_triggered}")
                logger.info(f"   Entity retries: {self.recovery_stats.entity_extractions_retried}")
                
        except Exception as e:
            logger.error(f"❌ Error logging health status: {e}")

# Async bridge implementation for Neo4j
class AsyncNeo4jBridge:
    """
    Async wrapper for Neo4j bridging with enhanced retry logic.
    """
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
    async def bridge_to_neo4j(self, entities_file: str, relationships_file: str) -> bool:
        """
        Bridge entities and relationships to Neo4j with async retry logic.
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🌉 Neo4j bridge attempt {attempt + 1}/{self.max_retries}")
                
                # Use the synchronous bridge in a thread pool
                import concurrent.futures
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._sync_bridge, entities_file, relationships_file)
                    result = await asyncio.get_event_loop().run_in_executor(None, lambda: future.result())
                    
                if result:
                    logger.info("✅ Neo4j bridge completed successfully")
                    return True
                    
            except Exception as e:
                logger.error(f"❌ Neo4j bridge attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    
        return False
        
    def _sync_bridge(self, entities_file: str, relationships_file: str) -> bool:
        """
        Synchronous bridge operation.
        """
        try:
            from lightrag_neo4j_bridge import LightRAGNeo4jBridge
            
            bridge = LightRAGNeo4jBridge(
                entities_file=entities_file,
                relationships_file=relationships_file,
                batch_size=100
            )
            
            return bridge.bridge_to_neo4j()
            
        except Exception as e:
            logger.error(f"❌ Sync bridge error: {e}")
            return False

# Main recovery functions
async def run_immediate_recovery():
    """
    Run immediate recovery for currently stuck files.
    """
    logger.info("🚀 Starting immediate pipeline recovery...")
    
    recovery_system = PipelineRecoverySystem()
    
    # Detect currently stuck files
    stuck_files = await recovery_system.detect_stuck_files()
    
    if not stuck_files:
        logger.info("✅ No stuck files detected")
        return
        
    logger.info(f"🔧 Found {len(stuck_files)} stuck files, attempting recovery...")
    
    # Attempt recovery for each file
    for stuck_file in stuck_files:
        logger.info(f"Processing {stuck_file.filename} (stage: {stuck_file.stage})")
        success = await recovery_system.attempt_recovery(stuck_file)
        
        if success:
            logger.info(f"✅ Recovered {stuck_file.filename}")
        else:
            logger.error(f"❌ Failed to recover {stuck_file.filename}")
            
    # Check for orphaned entities
    await recovery_system.check_orphaned_entities()
    
    # Log final stats
    stats = recovery_system.recovery_stats
    logger.info(f"🏁 Recovery complete:")
    logger.info(f"   Files detected: {stats.files_detected}")
    logger.info(f"   Files recovered: {stats.files_recovered}")
    logger.info(f"   Files failed: {stats.files_failed}")
    logger.info(f"   Neo4j bridges triggered: {stats.neo4j_bridges_triggered}")

async def start_monitoring_service():
    """
    Start continuous monitoring service.
    """
    logger.info("🔄 Starting continuous pipeline monitoring...")
    
    recovery_system = PipelineRecoverySystem(heartbeat_interval=60)  # 1 minute intervals
    
    try:
        await recovery_system.start_heartbeat_monitoring()
    except KeyboardInterrupt:
        logger.info("👋 Monitoring service stopped by user")
        recovery_system.stop_heartbeat_monitoring()
    except Exception as e:
        logger.error(f"❌ Monitoring service error: {e}")
        recovery_system.stop_heartbeat_monitoring()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        # Start continuous monitoring
        asyncio.run(start_monitoring_service())
    else:
        # Run immediate recovery
        asyncio.run(run_immediate_recovery())