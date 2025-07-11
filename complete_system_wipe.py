#!/usr/bin/env python3
"""
Complete System Wipe - Neo4j, NetworkX, and Local Documents
Clean slate for document-level context integration implementation
"""

import os
import shutil
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompleteSystemWipe:
    """Wipes all data stores for fresh start"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Neo4j connection
        self.uri = os.getenv('NEO4J_URI', 'neo4j+s://57ed0189.databases.neo4j.io')
        self.username = os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD')
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        
        # Project paths
        self.project_root = "/Users/johninniger/Workspace/line_lead_qsr_mvp"
        
    def complete_wipe(self):
        """Perform complete system wipe"""
        
        logger.info("🧹 Starting complete system wipe...")
        
        # 1. Wipe Neo4j database
        logger.info("Wiping Neo4j database...")
        self.wipe_neo4j()
        
        # 2. Wipe NetworkX storage
        logger.info("Wiping NetworkX storage...")
        self.wipe_networkx_storage()
        
        # 3. Wipe local documents library
        logger.info("Wiping local documents library...")
        self.wipe_local_documents()
        
        # 4. Clean up backend storage
        logger.info("Cleaning up backend storage...")
        self.cleanup_backend_storage()
        
        # 5. Reset document tracking files
        logger.info("Resetting document tracking...")
        self.reset_document_tracking()
        
        logger.info("✅ Complete system wipe finished - ready for fresh implementation")
        
    def wipe_neo4j(self):
        """Completely wipe Neo4j database"""
        
        with self.driver.session() as session:
            # Delete all relationships first
            query = """
            MATCH ()-[r]-()
            DELETE r
            RETURN count(r) as deleted_relationships
            """
            
            result = session.run(query)
            deleted_rels = result.single()['deleted_relationships']
            logger.info(f"Deleted {deleted_rels} relationships from Neo4j")
            
            # Delete all nodes
            query = """
            MATCH (n)
            DELETE n
            RETURN count(n) as deleted_nodes
            """
            
            result = session.run(query)
            deleted_nodes = result.single()['deleted_nodes']
            logger.info(f"Deleted {deleted_nodes} nodes from Neo4j")
            
            # Verify empty database
            query = """
            MATCH (n)
            RETURN count(n) as remaining_nodes
            """
            
            result = session.run(query)
            remaining = result.single()['remaining_nodes']
            
            if remaining == 0:
                logger.info("✅ Neo4j database completely wiped")
            else:
                logger.warning(f"⚠️ {remaining} nodes still remain in Neo4j")
                
    def wipe_networkx_storage(self):
        """Wipe NetworkX storage directories"""
        
        networkx_paths = [
            os.path.join(self.project_root, "rag_storage"),
            os.path.join(self.project_root, "backend", "rag_storage"),
            os.path.join(self.project_root, "backend", "data"),
            os.path.join(self.project_root, "data")
        ]
        
        for path in networkx_paths:
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    logger.info(f"Deleted NetworkX storage: {path}")
                except Exception as e:
                    logger.error(f"Error deleting {path}: {e}")
            else:
                logger.info(f"NetworkX storage not found: {path}")
                
    def wipe_local_documents(self):
        """Wipe local documents library"""
        
        document_paths = [
            os.path.join(self.project_root, "uploaded_docs"),
            os.path.join(self.project_root, "uploads"),
            os.path.join(self.project_root, "backend", "uploaded_docs"),
            os.path.join(self.project_root, "backend", "uploads"),
            os.path.join(self.project_root, "demo_files")
        ]
        
        for path in document_paths:
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    logger.info(f"Deleted document library: {path}")
                except Exception as e:
                    logger.error(f"Error deleting {path}: {e}")
            else:
                logger.info(f"Document library not found: {path}")
                
    def cleanup_backend_storage(self):
        """Clean up backend storage files"""
        
        # Clean up temp files
        temp_patterns = [
            "temp_extraction_*.json",
            "checkpoint_*.json", 
            "recovery_checkpoint_*.json",
            "bridge_checkpoint_*.json"
        ]
        
        backend_path = os.path.join(self.project_root, "backend")
        
        for pattern in temp_patterns:
            import glob
            temp_files = glob.glob(os.path.join(backend_path, pattern))
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                    logger.info(f"Deleted temp file: {os.path.basename(temp_file)}")
                except Exception as e:
                    logger.error(f"Error deleting {temp_file}: {e}")
                    
    def reset_document_tracking(self):
        """Reset document tracking files"""
        
        tracking_files = [
            os.path.join(self.project_root, "documents.json"),
            os.path.join(self.project_root, "backend", "neo4j_verified_documents.json")
        ]
        
        for tracking_file in tracking_files:
            if os.path.exists(tracking_file):
                try:
                    # Create empty tracking file
                    with open(tracking_file, 'w') as f:
                        if tracking_file.endswith('documents.json'):
                            import json
                            json.dump([], f)
                        else:
                            import json
                            json.dump({}, f)
                    logger.info(f"Reset tracking file: {os.path.basename(tracking_file)}")
                except Exception as e:
                    logger.error(f"Error resetting {tracking_file}: {e}")
                    
    def verify_wipe(self):
        """Verify that the wipe was successful"""
        
        logger.info("🔍 Verifying complete wipe...")
        
        # Check Neo4j
        with self.driver.session() as session:
            query = "MATCH (n) RETURN count(n) as node_count"
            result = session.run(query)
            node_count = result.single()['node_count']
            
            query = "MATCH ()-[r]-() RETURN count(r) as rel_count"
            result = session.run(query)
            rel_count = result.single()['rel_count']
            
            logger.info(f"Neo4j state: {node_count} nodes, {rel_count} relationships")
            
        # Check file systems
        storage_paths = [
            "rag_storage", "data", "uploaded_docs", "uploads", "demo_files"
        ]
        
        for path_name in storage_paths:
            full_path = os.path.join(self.project_root, path_name)
            exists = os.path.exists(full_path)
            logger.info(f"Storage path {path_name}: {'EXISTS' if exists else 'CLEAN'}")
            
        if node_count == 0 and rel_count == 0:
            logger.info("✅ System wipe verification successful - clean slate ready")
        else:
            logger.warning("⚠️ System wipe incomplete - some data remains")
            
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()

def main():
    """Main execution function"""
    
    wiper = CompleteSystemWipe()
    
    try:
        # Confirm before wiping
        response = input("⚠️  This will completely wipe Neo4j, NetworkX storage, and all documents. Are you sure? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            wiper.complete_wipe()
            wiper.verify_wipe()
        else:
            logger.info("Wipe cancelled by user")
            
    except KeyboardInterrupt:
        logger.info("Wipe interrupted by user")
    except Exception as e:
        logger.error(f"Wipe failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        wiper.close()

if __name__ == "__main__":
    main()