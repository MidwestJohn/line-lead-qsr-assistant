#!/usr/bin/env python3
"""
LightRAG Data Extractor
========================

Extract entities and relationships from LightRAG storage formats and prepare them for the bridge.
Handles various LightRAG storage formats and creates standardized JSON files.

Author: Generated with Memex (https://memex.tech)
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightRAGDataExtractor:
    """
    Extract data from various LightRAG storage formats.
    """
    
    def __init__(self, storage_path: str = "./rag_storage"):
        self.storage_path = Path(storage_path)
        self.entities = []
        self.relationships = []
    
    def find_storage_directories(self) -> List[Path]:
        """Find all potential LightRAG storage directories."""
        storage_dirs = []
        
        # Check current directory and subdirectories
        patterns = [
            "rag_storage*",
            "data/rag_storage*",
            "lightrag_*",
            "knowledge_graph*"
        ]
        
        for pattern in patterns:
            for path in glob.glob(str(self.storage_path.parent / pattern)):
                storage_dirs.append(Path(path))
        
        return storage_dirs
    
    def extract_from_json_files(self, storage_dir: Path) -> bool:
        """Extract from JSON files in storage directory."""
        try:
            # Look for common LightRAG JSON files
            json_files = [
                "entities.json",
                "relationships.json", 
                "graph_data.json",
                "knowledge_graph.json",
                "extracted_entities.json",
                "extracted_relationships.json"
            ]
            
            entities_found = False
            relationships_found = False
            
            for json_file in json_files:
                file_path = storage_dir / json_file
                if file_path.exists():
                    logger.info(f"Found JSON file: {file_path}")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Determine if this is entities or relationships
                    if "entities" in json_file.lower() or self._looks_like_entities(data):
                        self.entities.extend(self._normalize_entities(data))
                        entities_found = True
                        logger.info(f"Extracted {len(data)} entities from {json_file}")
                    
                    elif "relationships" in json_file.lower() or self._looks_like_relationships(data):
                        self.relationships.extend(self._normalize_relationships(data))
                        relationships_found = True
                        logger.info(f"Extracted {len(data)} relationships from {json_file}")
                    
                    elif "graph" in json_file.lower():
                        # Try to extract both from graph file
                        if isinstance(data, dict):
                            if "entities" in data:
                                self.entities.extend(self._normalize_entities(data["entities"]))
                                entities_found = True
                            if "relationships" in data:
                                self.relationships.extend(self._normalize_relationships(data["relationships"]))
                                relationships_found = True
                            if "nodes" in data:
                                self.entities.extend(self._normalize_entities(data["nodes"]))
                                entities_found = True
                            if "edges" in data:
                                self.relationships.extend(self._normalize_relationships(data["edges"]))
                                relationships_found = True
            
            return entities_found or relationships_found
            
        except Exception as e:
            logger.error(f"Error extracting from JSON files: {e}")
            return False
    
    def extract_from_graph_storage(self, storage_dir: Path) -> bool:
        """Extract from graph storage files."""
        try:
            # Look for graph storage files
            graph_files = list(storage_dir.glob("*.graph"))
            graph_files.extend(list(storage_dir.glob("graph_*.json")))
            
            for graph_file in graph_files:
                logger.info(f"Processing graph file: {graph_file}")
                
                with open(graph_file, 'r', encoding='utf-8') as f:
                    if graph_file.suffix == '.json':
                        data = json.load(f)
                        self._process_graph_data(data)
                    else:
                        # Try to parse as text/other format
                        content = f.read()
                        self._process_graph_text(content)
            
            return len(graph_files) > 0
            
        except Exception as e:
            logger.error(f"Error extracting from graph storage: {e}")
            return False
    
    def _looks_like_entities(self, data) -> bool:
        """Determine if data looks like entities."""
        if not isinstance(data, list) or not data:
            return False
        
        first_item = data[0]
        if not isinstance(first_item, dict):
            return False
        
        # Check for common entity fields
        entity_fields = ['name', 'type', 'label', 'description', 'id', 'entity_type']
        return any(field in first_item for field in entity_fields)
    
    def _looks_like_relationships(self, data) -> bool:
        """Determine if data looks like relationships."""
        if not isinstance(data, list) or not data:
            return False
        
        first_item = data[0]
        if not isinstance(first_item, dict):
            return False
        
        # Check for common relationship fields
        relationship_fields = ['source', 'target', 'from', 'to', 'start', 'end', 'relationship', 'rel_type']
        return any(field in first_item for field in relationship_fields)
    
    def _normalize_entities(self, entities_data) -> List[Dict]:
        """Normalize entities to standard format."""
        normalized = []
        
        if not isinstance(entities_data, list):
            entities_data = [entities_data] if isinstance(entities_data, dict) else []
        
        for entity in entities_data:
            if not isinstance(entity, dict):
                continue
            
            # Extract common fields
            normalized_entity = {
                'name': entity.get('name', entity.get('id', entity.get('entity_name', 'Unknown'))),
                'type': entity.get('type', entity.get('label', entity.get('entity_type', 'ENTITY'))),
                'description': entity.get('description', entity.get('desc', '')),
            }
            
            # Add all other fields
            for key, value in entity.items():
                if key not in ['name', 'type', 'description', 'id', 'label', 'entity_type', 'entity_name', 'desc']:
                    normalized_entity[key] = value
            
            normalized.append(normalized_entity)
        
        return normalized
    
    def _normalize_relationships(self, relationships_data) -> List[Dict]:
        """Normalize relationships to standard format."""
        normalized = []
        
        if not isinstance(relationships_data, list):
            relationships_data = [relationships_data] if isinstance(relationships_data, dict) else []
        
        for rel in relationships_data:
            if not isinstance(rel, dict):
                continue
            
            # Extract common fields
            normalized_rel = {
                'source': rel.get('source', rel.get('from', rel.get('start', rel.get('src')))),
                'target': rel.get('target', rel.get('to', rel.get('end', rel.get('dst')))),
                'type': rel.get('type', rel.get('relationship', rel.get('rel_type', 'RELATED_TO'))),
                'description': rel.get('description', rel.get('desc', '')),
            }
            
            # Skip if missing source or target
            if not normalized_rel['source'] or not normalized_rel['target']:
                continue
            
            # Add all other fields
            for key, value in rel.items():
                if key not in ['source', 'target', 'type', 'description', 'from', 'to', 'start', 'end', 'relationship', 'rel_type', 'src', 'dst', 'desc']:
                    normalized_rel[key] = value
            
            normalized.append(normalized_rel)
        
        return normalized
    
    def _process_graph_data(self, data: Dict):
        """Process graph data from JSON format."""
        if 'nodes' in data:
            self.entities.extend(self._normalize_entities(data['nodes']))
        if 'edges' in data:
            self.relationships.extend(self._normalize_relationships(data['edges']))
        if 'entities' in data:
            self.entities.extend(self._normalize_entities(data['entities']))
        if 'relationships' in data:
            self.relationships.extend(self._normalize_relationships(data['relationships']))
    
    def _process_graph_text(self, content: str):
        """Process graph data from text format."""
        # Try to parse as JSON first
        try:
            data = json.loads(content)
            self._process_graph_data(data)
            return
        except json.JSONDecodeError:
            pass
        
        # Try to extract entities and relationships from text
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for patterns like "Entity: name (type)"
            if line.startswith('Entity:'):
                # Extract entity information
                pass
            elif line.startswith('Relationship:'):
                # Extract relationship information
                pass
    
    def save_extracted_data(self, entities_file: str = "extracted_entities.json", 
                           relationships_file: str = "extracted_relationships.json"):
        """Save extracted data to JSON files."""
        try:
            # Remove duplicates
            unique_entities = []
            seen_entities = set()
            
            for entity in self.entities:
                entity_key = (entity['name'], entity['type'])
                if entity_key not in seen_entities:
                    unique_entities.append(entity)
                    seen_entities.add(entity_key)
            
            unique_relationships = []
            seen_relationships = set()
            
            for rel in self.relationships:
                rel_key = (rel['source'], rel['target'], rel['type'])
                if rel_key not in seen_relationships:
                    unique_relationships.append(rel)
                    seen_relationships.add(rel_key)
            
            # Save entities
            with open(entities_file, 'w', encoding='utf-8') as f:
                json.dump(unique_entities, f, indent=2, ensure_ascii=False)
            
            # Save relationships
            with open(relationships_file, 'w', encoding='utf-8') as f:
                json.dump(unique_relationships, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Extracted data saved:")
            logger.info(f"   - {entities_file}: {len(unique_entities)} entities")
            logger.info(f"   - {relationships_file}: {len(unique_relationships)} relationships")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving extracted data: {e}")
            return False
    
    def extract_all(self) -> bool:
        """Extract from all available storage formats."""
        logger.info("🔍 Searching for LightRAG storage directories...")
        
        storage_dirs = self.find_storage_directories()
        
        if not storage_dirs:
            logger.warning("No LightRAG storage directories found")
            return False
        
        logger.info(f"Found {len(storage_dirs)} storage directories:")
        for storage_dir in storage_dirs:
            logger.info(f"  - {storage_dir}")
        
        total_extracted = False
        
        for storage_dir in storage_dirs:
            logger.info(f"\n🔄 Processing storage directory: {storage_dir}")
            
            if not storage_dir.exists():
                logger.warning(f"Directory does not exist: {storage_dir}")
                continue
            
            # Try JSON files first
            if self.extract_from_json_files(storage_dir):
                total_extracted = True
            
            # Try graph storage files
            if self.extract_from_graph_storage(storage_dir):
                total_extracted = True
        
        if total_extracted:
            logger.info(f"\n📊 Total extracted:")
            logger.info(f"   - Entities: {len(self.entities)}")
            logger.info(f"   - Relationships: {len(self.relationships)}")
        
        return total_extracted

def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract LightRAG data for Neo4j bridge")
    parser.add_argument("--storage", "-s", help="LightRAG storage directory", default="./rag_storage")
    parser.add_argument("--entities", "-e", help="Output entities file", default="extracted_entities.json")
    parser.add_argument("--relationships", "-r", help="Output relationships file", default="extracted_relationships.json")
    
    args = parser.parse_args()
    
    extractor = LightRAGDataExtractor(args.storage)
    
    if extractor.extract_all():
        if extractor.save_extracted_data(args.entities, args.relationships):
            print("✅ Data extraction completed successfully!")
            print(f"📁 Files created:")
            print(f"   - {args.entities}")
            print(f"   - {args.relationships}")
        else:
            print("❌ Failed to save extracted data")
    else:
        print("❌ No data found to extract")

if __name__ == "__main__":
    main()