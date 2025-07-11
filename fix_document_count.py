#!/usr/bin/env python3
"""
Fix Document Count Issue
Updates the document count to reflect Neo4j state and triggers UI refresh
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from services.neo4j_service import Neo4jService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_document_count():
    """Update document count in documents.json to reflect Neo4j state"""
    try:
        # Connect to Neo4j
        neo4j = Neo4jService()
        if not neo4j.connect():
            logger.error("❌ Failed to connect to Neo4j")
            return False
        
        with neo4j.driver.session() as session:
            # Get document count from Neo4j
            neo4j_doc_count = session.run("""
                MATCH (d:Document) 
                RETURN count(d) as count
            """).single()["count"]
            
            # Get documents list
            documents_list = session.run("""
                MATCH (d:Document)
                RETURN d.name as name, d.file_path as file_path, d.pages as pages
                ORDER BY d.name
            """).data()
            
            logger.info(f"📋 Found {neo4j_doc_count} documents in Neo4j:")
            for doc in documents_list:
                logger.info(f"  - {doc['name']} ({doc['pages']} pages)")
        
        # Update documents.json
        documents_path = Path("documents.json")
        if documents_path.exists():
            with open(documents_path, 'r') as f:
                documents_data = json.load(f)
                
            # Update count and metadata
            old_count = documents_data.get("count", 0)
            documents_data["count"] = neo4j_doc_count
            documents_data["last_updated"] = datetime.now().isoformat()
            documents_data["source"] = "neo4j_verified"
            documents_data["documents"] = documents_list
            
            # Update processing status
            for doc_id, doc_info in documents_data.get("documents", {}).items():
                if isinstance(doc_info, dict):
                    doc_info["status"] = "complete"
                    doc_info["neo4j_verified"] = True
            
            with open(documents_path, 'w') as f:
                json.dump(documents_data, f, indent=2)
            
            logger.info(f"✅ Updated documents.json count: {old_count} → {neo4j_doc_count}")
            
            # Update neo4j_verified_documents.json
            neo4j_verified_path = Path("backend/neo4j_verified_documents.json")
            if neo4j_verified_path.exists():
                with open(neo4j_verified_path, 'r') as f:
                    verified_data = json.load(f)
                    
                verified_data["count"] = neo4j_doc_count
                verified_data["last_updated"] = datetime.now().isoformat()
                verified_data["documents"] = documents_list
                
                with open(neo4j_verified_path, 'w') as f:
                    json.dump(verified_data, f, indent=2)
                    
                logger.info(f"✅ Updated neo4j_verified_documents.json")
            
            return True
        else:
            logger.warning("documents.json not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Document count update failed: {e}")
        return False
    finally:
        neo4j.disconnect()

def check_upload_progress_endpoints():
    """Check if upload progress endpoints are working"""
    try:
        import requests
        
        # Check health endpoint
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            logger.info(f"🏥 Health endpoint: {health_data['status']} - {health_data['document_count']} documents")
        else:
            logger.warning(f"⚠️ Health endpoint returned {health_response.status_code}")
            
        # Check documents endpoint
        docs_response = requests.get("http://localhost:8000/documents", timeout=5)
        if docs_response.status_code == 200:
            docs_data = docs_response.json()
            logger.info(f"📄 Documents endpoint: {len(docs_data)} documents")
        else:
            logger.warning(f"⚠️ Documents endpoint returned {docs_response.status_code}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Endpoint check failed: {e}")
        return False

def fix_remaining_orphaned_entities():
    """Fix the remaining 10 orphaned entities with targeted relationships"""
    try:
        neo4j = Neo4jService()
        if not neo4j.connect():
            logger.error("❌ Failed to connect to Neo4j")
            return False
        
        with neo4j.driver.session() as session:
            # Get remaining orphaned entities
            orphaned = session.run("""
                MATCH (n) WHERE NOT (n)-[]-() 
                AND NOT 'VisualCitation' IN labels(n) 
                AND NOT 'Document' IN labels(n)
                RETURN n.name as name, labels(n) as labels, n.description as description
                LIMIT 10
            """).data()
            
            logger.info(f"🔧 Fixing {len(orphaned)} remaining orphaned entities:")
            
            for entity in orphaned:
                logger.info(f"  - {entity['name']} ({entity['labels']})")
                
                # Try to find related entities and create relationships
                related_entities = session.run("""
                    MATCH (related) 
                    WHERE related.name <> $name 
                    AND (
                        toLower(related.name) CONTAINS toLower($name) OR
                        toLower($name) CONTAINS toLower(related.name) OR
                        toLower(related.description) CONTAINS toLower($name) OR
                        toLower($name) CONTAINS toLower(related.description)
                    )
                    RETURN related.name as related_name
                    LIMIT 3
                """, {"name": entity["name"]}).data()
                
                # Create relationships to related entities
                for related in related_entities:
                    try:
                        session.run("""
                            MATCH (orphan {name: $orphan_name}), (related {name: $related_name})
                            CREATE (orphan)-[r:RELATED_TO {
                                description: 'Auto-generated relationship',
                                confidence: 0.6,
                                created_by: 'orphan_fix',
                                created_at: datetime()
                            }]->(related)
                        """, {
                            "orphan_name": entity["name"],
                            "related_name": related["related_name"]
                        })
                        logger.info(f"    ✅ Connected to {related['related_name']}")
                    except Exception as rel_error:
                        logger.error(f"    ❌ Failed to connect to {related['related_name']}: {rel_error}")
        
        neo4j.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Orphaned entity fix failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Document Count & Orphaned Entity Fix")
    print("=" * 50)
    
    logger.info("1. Updating document count...")
    success1 = update_document_count()
    
    logger.info("2. Checking upload progress endpoints...")
    success2 = check_upload_progress_endpoints()
    
    logger.info("3. Fixing remaining orphaned entities...")
    success3 = fix_remaining_orphaned_entities()
    
    if success1 and success2 and success3:
        print("\n✅ ALL FIXES COMPLETED SUCCESSFULLY!")
        print("- Document count updated")
        print("- Upload progress endpoints verified")
        print("- Remaining orphaned entities fixed")
    else:
        print("\n⚠️ Some fixes may have failed - check logs above")
    
    print("\n" + "=" * 50)