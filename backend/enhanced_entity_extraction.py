#!/usr/bin/env python3
"""
Enhanced Entity Extraction for Stuck Files
==========================================

Specialized extraction service to handle files stuck in text extraction phase.
Uses chunked processing and enhanced retry logic for reliability.

Author: Generated with Memex (https://memex.tech)
Co-Authored-By: Memex <noreply@memex.tech>
"""

import asyncio
import json
import logging
import time
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedEntityExtractor:
    """
    Enhanced entity extraction for files that are stuck in processing.
    """
    
    def __init__(self, backend_dir: str = "/Users/johninniger/Workspace/line_lead_qsr_mvp/backend"):
        self.backend_dir = Path(backend_dir)
        
    async def extract_entities_for_document(self, document_id: str, text_content: str, filename: str) -> Tuple[bool, Dict]:
        """
        Extract entities and relationships for a specific document.
        """
        try:
            logger.info(f"🔄 Starting enhanced entity extraction for {filename}")
            
            # Use chunked processing for reliability
            entities, relationships = await self._extract_with_chunking(
                text_content, 
                filename,
                chunk_size=3000  # Larger chunks for better context
            )
            
            if entities or relationships:
                # Save extraction results
                extraction_file = self.backend_dir / f"temp_extraction_enhanced_{document_id}_{int(time.time())}.json"
                
                extraction_data = {
                    'entities': entities,
                    'relationships': relationships,
                    'document_id': document_id,
                    'filename': filename,
                    'extraction_time': datetime.now().isoformat(),
                    'extraction_method': 'enhanced_recovery',
                    'total_entities': len(entities),
                    'total_relationships': len(relationships)
                }
                
                with open(extraction_file, 'w') as f:
                    json.dump(extraction_data, f, indent=2)
                    
                logger.info(f"✅ Enhanced extraction complete: {len(entities)} entities, {len(relationships)} relationships")
                logger.info(f"Saved to: {extraction_file}")
                
                return True, extraction_data
            else:
                logger.warning(f"⚠️ No entities extracted for {filename}")
                return False, {}
                
        except Exception as e:
            logger.error(f"❌ Enhanced extraction failed for {filename}: {e}")
            logger.error(traceback.format_exc())
            return False, {}
            
    async def _extract_with_chunking(self, text: str, filename: str, chunk_size: int = 3000) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract entities using chunked processing for better reliability.
        """
        all_entities = []
        all_relationships = []
        
        try:
            # Split text into overlapping chunks for better context
            chunks = self._create_overlapping_chunks(text, chunk_size, overlap=500)
            
            logger.info(f"Processing {len(chunks)} chunks for {filename}")
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                try:
                    # Extract entities from chunk
                    chunk_entities = await self._extract_qsr_entities(chunk, f"{filename}_chunk_{i+1}")
                    chunk_relationships = await self._extract_qsr_relationships(chunk, chunk_entities, f"{filename}_chunk_{i+1}")
                    
                    all_entities.extend(chunk_entities)
                    all_relationships.extend(chunk_relationships)
                    
                    # Small delay between chunks to avoid overwhelming
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Chunk {i+1} extraction failed: {e}")
                    continue
                    
            # Deduplicate entities and relationships
            all_entities = self._deduplicate_entities(all_entities)
            all_relationships = self._deduplicate_relationships(all_relationships)
            
            logger.info(f"Extraction complete: {len(all_entities)} unique entities, {len(all_relationships)} unique relationships")
            
        except Exception as e:
            logger.error(f"❌ Chunked extraction error: {e}")
            
        return all_entities, all_relationships
        
    def _create_overlapping_chunks(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Create overlapping chunks for better context preservation.
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + (chunk_size // 2):  # Only if break point is reasonable
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1
                    
            chunks.append(chunk.strip())
            start = end - overlap
            
        return [chunk for chunk in chunks if len(chunk.strip()) > 100]  # Filter out tiny chunks
        
    async def _extract_qsr_entities(self, text: str, context: str) -> List[Dict]:
        """
        Extract QSR-specific entities from text.
        """
        entities = []
        
        try:
            # QSR Equipment patterns
            equipment_keywords = [
                'ice cream machine', 'freezer', 'fryer', 'grill', 'oven', 'mixer', 'blender',
                'dispenser', 'warmer', 'cooler', 'refrigerator', 'steamer', 'toaster',
                'slicer', 'scale', 'timer', 'thermometer', 'cleaning equipment', 'sanitizer',
                'cash register', 'POS system', 'drive-thru', 'headset', 'microphone'
            ]
            
            # Safety Equipment patterns  
            safety_keywords = [
                'fire extinguisher', 'first aid', 'safety equipment', 'protective gear',
                'gloves', 'goggles', 'apron', 'non-slip shoes', 'safety mat'
            ]
            
            # Process patterns
            process_keywords = [
                'cleaning', 'sanitizing', 'maintenance', 'inspection', 'calibration',
                'temperature check', 'inventory', 'training', 'procedure', 'protocol',
                'schedule', 'checklist', 'log', 'record', 'documentation'
            ]
            
            # Extract entities using patterns
            text_lower = text.lower()
            
            # Equipment entities
            for keyword in equipment_keywords:
                if keyword in text_lower:
                    entities.append({
                        'name': keyword,
                        'type': 'EQUIPMENT',
                        'description': f"QSR equipment mentioned in {context}: {keyword}",
                        'source': 'enhanced_extraction',
                        'confidence': 0.8,
                        'visual_refs': [self._generate_hash(keyword + context)]
                    })
                    
            # Safety entities
            for keyword in safety_keywords:
                if keyword in text_lower:
                    entities.append({
                        'name': keyword,
                        'type': 'SAFETY_EQUIPMENT',
                        'description': f"Safety equipment mentioned in {context}: {keyword}",
                        'source': 'enhanced_extraction',
                        'confidence': 0.8,
                        'visual_refs': [self._generate_hash(keyword + context)]
                    })
                    
            # Process entities
            for keyword in process_keywords:
                if keyword in text_lower:
                    entities.append({
                        'name': keyword,
                        'type': 'PROCESS',
                        'description': f"QSR process mentioned in {context}: {keyword}",
                        'source': 'enhanced_extraction',
                        'confidence': 0.7,
                        'visual_refs': [self._generate_hash(keyword + context)]
                    })
                    
            # Extract numerical measurements
            import re
            
            # Temperature patterns
            temp_patterns = re.findall(r'(\d+)\s*°?[FfCc]', text)
            for temp in temp_patterns:
                entities.append({
                    'name': f"{temp}°F",
                    'type': 'TEMPERATURE',
                    'description': f"Temperature measurement from {context}",
                    'source': 'enhanced_extraction',
                    'confidence': 0.9,
                    'visual_refs': [self._generate_hash(temp + context)]
                })
                
            # Time patterns  
            time_patterns = re.findall(r'(\d+)\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)', text, re.IGNORECASE)
            for time_val, unit in time_patterns:
                entities.append({
                    'name': f"{time_val} {unit}",
                    'type': 'TIME_DURATION',
                    'description': f"Time duration from {context}",
                    'source': 'enhanced_extraction',
                    'confidence': 0.8,
                    'visual_refs': [self._generate_hash(time_val + unit + context)]
                })
                
        except Exception as e:
            logger.error(f"❌ Entity extraction error: {e}")
            
        return entities
        
    async def _extract_qsr_relationships(self, text: str, entities: List[Dict], context: str) -> List[Dict]:
        """
        Extract relationships between entities.
        """
        relationships = []
        
        try:
            # Create relationships between equipment and processes
            equipment_entities = [e for e in entities if e['type'] == 'EQUIPMENT']
            process_entities = [e for e in entities if e['type'] == 'PROCESS']
            safety_entities = [e for e in entities if e['type'] == 'SAFETY_EQUIPMENT']
            
            # Equipment → Process relationships
            for equipment in equipment_entities:
                for process in process_entities:
                    if self._entities_related_in_text(equipment['name'], process['name'], text):
                        relationships.append({
                            'source': equipment['name'],
                            'target': process['name'],
                            'relationship': 'REQUIRES',
                            'description': f"{equipment['name']} requires {process['name']}",
                            'source_id': equipment.get('visual_refs', [''])[0],
                            'target_id': process.get('visual_refs', [''])[0],
                            'weight': 0.8,
                            'context': context
                        })
                        
            # Equipment → Safety relationships
            for equipment in equipment_entities:
                for safety in safety_entities:
                    if self._entities_related_in_text(equipment['name'], safety['name'], text):
                        relationships.append({
                            'source': equipment['name'],
                            'target': safety['name'],
                            'relationship': 'USES',
                            'description': f"{equipment['name']} uses {safety['name']}",
                            'source_id': equipment.get('visual_refs', [''])[0],
                            'target_id': safety.get('visual_refs', [''])[0],
                            'weight': 0.7,
                            'context': context
                        })
                        
        except Exception as e:
            logger.error(f"❌ Relationship extraction error: {e}")
            
        return relationships
        
    def _entities_related_in_text(self, entity1: str, entity2: str, text: str, window: int = 200) -> bool:
        """
        Check if two entities appear near each other in text.
        """
        text_lower = text.lower()
        entity1_lower = entity1.lower()
        entity2_lower = entity2.lower()
        
        # Find all occurrences of entity1
        start = 0
        while True:
            pos1 = text_lower.find(entity1_lower, start)
            if pos1 == -1:
                break
                
            # Check if entity2 appears within window
            window_start = max(0, pos1 - window)
            window_end = min(len(text), pos1 + len(entity1_lower) + window)
            window_text = text_lower[window_start:window_end]
            
            if entity2_lower in window_text:
                return True
                
            start = pos1 + 1
            
        return False
        
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        Remove duplicate entities based on name and type.
        """
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = (entity['name'].lower(), entity['type'])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
                
        return unique_entities
        
    def _deduplicate_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """
        Remove duplicate relationships.
        """
        seen = set()
        unique_relationships = []
        
        for rel in relationships:
            key = (rel['source'].lower(), rel['target'].lower(), rel['relationship'])
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)
                
        return unique_relationships
        
    def _generate_hash(self, text: str) -> str:
        """
        Generate a hash for entity referencing.
        """
        return hashlib.md5(text.encode()).hexdigest()[:8]

async def process_stuck_files():
    """
    Process all files that are stuck in text extraction.
    """
    logger.info("🚀 Starting enhanced entity extraction for stuck files...")
    
    try:
        # Load documents database
        backend_dir = Path("/Users/johninniger/Workspace/line_lead_qsr_mvp/backend")
        docs_db_path = backend_dir.parent / "documents.json"
        
        with open(docs_db_path, 'r') as f:
            docs_db = json.load(f)
            
        # Initialize extractor
        extractor = EnhancedEntityExtractor()
        
        # Find stuck files
        stuck_files = []
        for doc_id, doc_info in docs_db.items():
            # Check if file has text but no temp extraction
            if doc_info.get('text_content') and not any(
                Path(backend_dir / f"temp_extraction_*{doc_id}*.json").exists() 
                for pattern in [f"temp_extraction_*{doc_id}*.json"]
            ):
                temp_files = list(backend_dir.glob(f"temp_extraction_*{doc_id}*.json"))
                if not temp_files:
                    stuck_files.append((doc_id, doc_info))
                    
        logger.info(f"Found {len(stuck_files)} files stuck in text extraction")
        
        # Process each stuck file
        for doc_id, doc_info in stuck_files:
            filename = doc_info['original_filename']
            text_content = doc_info['text_content']
            
            logger.info(f"Processing {filename}...")
            
            success, extraction_data = await extractor.extract_entities_for_document(
                doc_id, text_content, filename
            )
            
            if success:
                logger.info(f"✅ Successfully processed {filename}")
                
                # Immediately bridge to Neo4j
                await bridge_extraction_to_neo4j(extraction_data, doc_id)
            else:
                logger.error(f"❌ Failed to process {filename}")
                
        logger.info("🏁 Enhanced extraction complete")
        
    except Exception as e:
        logger.error(f"❌ Enhanced extraction error: {e}")
        logger.error(traceback.format_exc())

async def bridge_extraction_to_neo4j(extraction_data: Dict, document_id: str):
    """
    Bridge extraction data directly to Neo4j.
    """
    try:
        logger.info(f"🌉 Bridging extraction to Neo4j for {extraction_data['filename']}")
        
        from lightrag_neo4j_bridge import LightRAGNeo4jBridge
        
        backend_dir = Path("/Users/johninniger/Workspace/line_lead_qsr_mvp/backend")
        
        # Create temporary files
        temp_entities_file = backend_dir / f"temp_bridge_entities_{document_id}.json"
        temp_relationships_file = backend_dir / f"temp_bridge_relationships_{document_id}.json"
        
        with open(temp_entities_file, 'w') as f:
            json.dump(extraction_data['entities'], f, indent=2)
            
        with open(temp_relationships_file, 'w') as f:
            json.dump(extraction_data['relationships'], f, indent=2)
            
        # Initialize bridge
        bridge = LightRAGNeo4jBridge(
            entities_file=str(temp_entities_file),
            relationships_file=str(temp_relationships_file),
            batch_size=50,
            checkpoint_file=f"bridge_checkpoint_{document_id}.json"
        )
        
        # Execute bridging
        success = await bridge.bridge_to_neo4j_async()
        
        # Cleanup temporary files
        temp_entities_file.unlink(missing_ok=True)
        temp_relationships_file.unlink(missing_ok=True)
        
        if success:
            # Create completion checkpoint
            checkpoint_file = backend_dir / f"checkpoint_{int(time.time())}.json"
            checkpoint_data = {
                'document_id': document_id,
                'filename': extraction_data['filename'],
                'entities_bridged': len(extraction_data['entities']),
                'relationships_bridged': len(extraction_data['relationships']),
                'completion_time': datetime.now().isoformat(),
                'extraction_method': 'enhanced_recovery'
            }
            
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
                
            logger.info(f"✅ Successfully bridged {len(extraction_data['entities'])} entities to Neo4j")
        else:
            logger.error(f"❌ Failed to bridge extraction to Neo4j")
            
    except Exception as e:
        logger.error(f"❌ Neo4j bridging error: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(process_stuck_files())