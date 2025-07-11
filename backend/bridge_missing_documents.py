#!/usr/bin/env python3
"""
Bridge Missing Documents to Neo4j
=================================

Manually bridge the 3 missing documents to Neo4j so they appear in the library.
"""

import json
import os
from services.neo4j_service import Neo4jService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def bridge_documents_to_neo4j():
    """Bridge the missing documents to Neo4j"""
    
    missing_docs = [
        {
            'doc_id': '2dc34b0a-a5e3-4fe0-aeb4-96e5101180a5',
            'filename': 'Taylor_C602_Service_manual.pdf',
            'extraction_file': 'temp_extraction_auto_proc_2dc34b0a-a5e3-4fe0-aeb4-96e5101180a5_1751982307.json'
        },
        {
            'doc_id': '62d1c2c4-6078-4503-ac5f-5fcaa8b86214', 
            'filename': 'test_qsr_doc.txt',
            'extraction_file': 'temp_extraction_enhanced_62d1c2c4-6078-4503-ac5f-5fcaa8b86214_1752024165.json'
        },
        {
            'doc_id': 'eb0cc949-3f44-4416-8746-6c7a003b7c6a',
            'filename': 'FCS-650256.pdf',
            'extraction_file': 'temp_extraction_enhanced_eb0cc949-3f44-4416-8746-6c7a003b7c6a_1752024169.json'
        }
    ]
    
    print("🌉 BRIDGING MISSING DOCUMENTS TO NEO4J")
    print("=" * 50)
    
    neo4j = Neo4jService()
    neo4j.connect()
    
    success_count = 0
    
    try:
        for doc in missing_docs:
            print(f"\n🔄 Processing {doc['filename']}...")
            
            # Load extraction data
            with open(doc['extraction_file'], 'r') as f:
                extraction_data = json.load(f)
            
            entities = extraction_data.get('entities', [])
            relationships = extraction_data.get('relationships', [])
            
            print(f"   Found: {len(entities)} entities, {len(relationships)} relationships")
            
            if len(entities) > 0:
                # Create Document node first
                with neo4j.driver.session() as session:
                    # Create the Document node
                    doc_query = """
                    MERGE (d:Document {
                        filename: $filename,
                        document_id: $doc_id,
                        processing_timestamp: $timestamp
                    })
                    SET d.entity_count = $entity_count,
                        d.relationship_count = $relationship_count
                    RETURN d
                    """
                    
                    session.run(doc_query, {
                        'filename': f"{doc['doc_id']}_{doc['filename']}",
                        'doc_id': doc['doc_id'][:12],  # Shortened ID 
                        'timestamp': '2025-07-09T15:52:00.000000',
                        'entity_count': len(entities),
                        'relationship_count': len(relationships)
                    })
                    
                    print(f"   ✅ Created Document node")
                    
                    # Create entities in batches
                    batch_size = 50
                    entity_batches = [entities[i:i + batch_size] for i in range(0, len(entities), batch_size)]
                    
                    entities_created = 0
                    for batch in entity_batches:
                        entity_query = """
                        UNWIND $entities AS entity
                        MERGE (e:ENTITY {name: entity.name})
                        SET e.type = entity.type,
                            e.description = coalesce(entity.description, ''),
                            e.document_source = $doc_id
                        """
                        
                        session.run(entity_query, {
                            'entities': batch,
                            'doc_id': doc['doc_id'][:12]
                        })
                        entities_created += len(batch)
                    
                    print(f"   ✅ Created {entities_created} entities")
                    
                    # Create relationships if any
                    if relationships:
                        rel_batches = [relationships[i:i + batch_size] for i in range(0, len(relationships), batch_size)]
                        relationships_created = 0
                        
                        for batch in rel_batches:
                            rel_query = """
                            UNWIND $relationships AS rel
                            MATCH (a:ENTITY {name: rel.source})
                            MATCH (b:ENTITY {name: rel.target})
                            MERGE (a)-[r:RELATED {type: coalesce(rel.type, 'RELATED')}]->(b)
                            SET r.description = coalesce(rel.description, ''),
                                r.document_source = $doc_id
                            """
                            
                            session.run(rel_query, {
                                'relationships': batch,
                                'doc_id': doc['doc_id'][:12]
                            })
                            relationships_created += len(batch)
                        
                        print(f"   ✅ Created {relationships_created} relationships")
                    
                    success_count += 1
                    print(f"   🎉 Successfully bridged {doc['filename']}")
            
            else:
                print(f"   ❌ No entities found")
    
    except Exception as e:
        logger.error(f"Error bridging documents: {e}")
    
    finally:
        neo4j.disconnect()
    
    print(f"\n🎯 BRIDGING SUMMARY: {success_count}/3 documents successfully bridged")
    return success_count

if __name__ == "__main__":
    result = bridge_documents_to_neo4j()
    
    if result > 0:
        print("\n✅ SUCCESS! Running integrity check to update library...")
        
        # Run the integrity enforcement again to pick up the new documents
        import subprocess
        subprocess.run(['python', 'enforce_neo4j_data_integrity.py'])
        
        print("🎯 Library should now show all 5 documents!")
    else:
        print("\n❌ No documents were successfully bridged")