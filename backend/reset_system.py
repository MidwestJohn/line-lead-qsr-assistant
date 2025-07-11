#!/usr/bin/env python3
"""
Complete System Reset Script
Wipes all data for clean slate testing:
- Neo4j: All nodes, relationships, constraints, indexes
- LightRAG storage: All embeddings, entities, relationships
- Upload directories: All uploaded documents
- Log files: Archive existing, start fresh
"""

import os
import shutil
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.rag')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemResetManager:
    """Manages complete system reset for clean slate testing."""
    
    def __init__(self):
        self.reset_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = f"./system_backup_{self.reset_timestamp}"
        
    async def reset_neo4j_database(self):
        """Complete Neo4j database wipe."""
        logger.info("🔥 RESETTING NEO4J DATABASE")
        
        try:
            from services.neo4j_service import neo4j_service
            
            # Connect to Neo4j
            if not neo4j_service.connected:
                neo4j_service.connect()
            
            # Get pre-reset statistics
            pre_stats = await neo4j_service.get_graph_statistics()
            logger.info(f"Pre-reset: {pre_stats.get('total_nodes', 0)} nodes, {pre_stats.get('total_relationships', 0)} relationships")
            
            # Drop all constraints and indexes
            logger.info("Dropping all constraints and indexes...")
            constraints_result = neo4j_service.execute_query("SHOW CONSTRAINTS")
            if constraints_result.get('success'):
                for constraint in constraints_result.get('records', []):
                    constraint_name = constraint.get('name', '')
                    if constraint_name:
                        neo4j_service.execute_query(f"DROP CONSTRAINT {constraint_name}")
                        logger.info(f"Dropped constraint: {constraint_name}")
            
            indexes_result = neo4j_service.execute_query("SHOW INDEXES")
            if indexes_result.get('success'):
                for index in indexes_result.get('records', []):
                    index_name = index.get('name', '')
                    if index_name and not index_name.startswith('system'):
                        neo4j_service.execute_query(f"DROP INDEX {index_name}")
                        logger.info(f"Dropped index: {index_name}")
            
            # Delete all relationships
            logger.info("Deleting all relationships...")
            rel_result = neo4j_service.execute_query("MATCH ()-[r]->() DELETE r")
            logger.info(f"Deleted relationships: {rel_result.get('success', False)}")
            
            # Delete all nodes
            logger.info("Deleting all nodes...")
            node_result = neo4j_service.execute_query("MATCH (n) DELETE n")
            logger.info(f"Deleted nodes: {node_result.get('success', False)}")
            
            # Verify cleanup
            post_stats = await neo4j_service.get_graph_statistics()
            logger.info(f"Post-reset: {post_stats.get('total_nodes', 0)} nodes, {post_stats.get('total_relationships', 0)} relationships")
            
            if post_stats.get('total_nodes', 0) == 0 and post_stats.get('total_relationships', 0) == 0:
                logger.info("✅ Neo4j database completely wiped")
                return True
            else:
                logger.error("❌ Neo4j database not completely wiped")
                return False
                
        except Exception as e:
            logger.error(f"❌ Neo4j reset failed: {e}")
            return False
    
    def reset_lightrag_storage(self):
        """Wipe all LightRAG storage directories."""
        logger.info("🔥 RESETTING LIGHTRAG STORAGE")
        
        storage_dirs = [
            "./rag_storage",
            "./rag_storage_optimized",
            "./rag_storage_test",
            "./rag_storage_qsr_optimized"
        ]
        
        reset_success = True
        
        for storage_dir in storage_dirs:
            if os.path.exists(storage_dir):
                try:
                    # Backup before deletion
                    backup_path = os.path.join(self.backup_dir, f"lightrag_storage_{os.path.basename(storage_dir)}")
                    os.makedirs(self.backup_dir, exist_ok=True)
                    shutil.copytree(storage_dir, backup_path)
                    logger.info(f"📦 Backed up {storage_dir} to {backup_path}")
                    
                    # Delete storage directory
                    shutil.rmtree(storage_dir)
                    logger.info(f"🗑️  Deleted {storage_dir}")
                    
                    # Recreate empty directory
                    os.makedirs(storage_dir, exist_ok=True)
                    logger.info(f"📁 Recreated empty {storage_dir}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to reset {storage_dir}: {e}")
                    reset_success = False
            else:
                logger.info(f"📁 {storage_dir} does not exist, skipping")
        
        if reset_success:
            logger.info("✅ LightRAG storage completely wiped")
        else:
            logger.error("❌ Some LightRAG storage directories failed to reset")
            
        return reset_success
    
    def reset_upload_directories(self):
        """Clear all uploaded documents."""
        logger.info("🔥 RESETTING UPLOAD DIRECTORIES")
        
        upload_dirs = [
            "./uploaded_docs",
            "./uploads",
            "../uploads",
            "./demo_files"
        ]
        
        reset_success = True
        
        for upload_dir in upload_dirs:
            if os.path.exists(upload_dir):
                try:
                    # Count files before deletion
                    file_count = len([f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))])
                    logger.info(f"📊 Found {file_count} files in {upload_dir}")
                    
                    # Backup before deletion
                    if file_count > 0:
                        backup_path = os.path.join(self.backup_dir, f"uploads_{os.path.basename(upload_dir)}")
                        os.makedirs(self.backup_dir, exist_ok=True)
                        shutil.copytree(upload_dir, backup_path)
                        logger.info(f"📦 Backed up {upload_dir} to {backup_path}")
                    
                    # Delete all files
                    for filename in os.listdir(upload_dir):
                        file_path = os.path.join(upload_dir, filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            logger.info(f"🗑️  Deleted {filename}")
                    
                    logger.info(f"✅ Cleared {upload_dir}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to reset {upload_dir}: {e}")
                    reset_success = False
            else:
                logger.info(f"📁 {upload_dir} does not exist, skipping")
        
        return reset_success
    
    def archive_log_files(self):
        """Archive existing log files and start fresh."""
        logger.info("🔥 ARCHIVING LOG FILES")
        
        log_files = [
            "backend.log",
            "frontend.log",
            "lightrag_neo4j_bridge.log",
            "backend_rag_debug.log",
            "backend_neo4j_working.log"
        ]
        
        # Create logs backup directory
        logs_backup_dir = os.path.join(self.backup_dir, "logs")
        os.makedirs(logs_backup_dir, exist_ok=True)
        
        archived_count = 0
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    # Copy to backup
                    backup_path = os.path.join(logs_backup_dir, f"{log_file}.{self.reset_timestamp}")
                    shutil.copy2(log_file, backup_path)
                    logger.info(f"📦 Archived {log_file} to {backup_path}")
                    
                    # Clear original log file
                    with open(log_file, 'w') as f:
                        f.write(f"# Log file reset at {datetime.now().isoformat()}\n")
                    
                    archived_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to archive {log_file}: {e}")
        
        logger.info(f"✅ Archived {archived_count} log files")
        return archived_count > 0
    
    def reset_cache_files(self):
        """Clear any cache files and temporary data."""
        logger.info("🔥 RESETTING CACHE FILES")
        
        cache_files = [
            "documents.json",
            "entity_test_response.json",
            "step_response.json",
            "final_step_response.json",
            "extraction_comparison_report.json",
            "cleanup_summary_*.json",
            "validation_results_*.json"
        ]
        
        deleted_count = 0
        
        for cache_pattern in cache_files:
            if '*' in cache_pattern:
                # Handle wildcard patterns
                import glob
                for file_path in glob.glob(cache_pattern):
                    try:
                        os.remove(file_path)
                        logger.info(f"🗑️  Deleted {file_path}")
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"❌ Failed to delete {file_path}: {e}")
            else:
                # Handle exact file names
                if os.path.exists(cache_pattern):
                    try:
                        os.remove(cache_pattern)
                        logger.info(f"🗑️  Deleted {cache_pattern}")
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"❌ Failed to delete {cache_pattern}: {e}")
        
        logger.info(f"✅ Deleted {deleted_count} cache files")
        return True
    
    async def complete_system_reset(self):
        """Execute complete system reset."""
        logger.info("🔥 STARTING COMPLETE SYSTEM RESET")
        logger.info("=" * 60)
        
        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
        logger.info(f"📦 Created backup directory: {self.backup_dir}")
        
        reset_results = {}
        
        # Reset Neo4j database
        reset_results['neo4j'] = await self.reset_neo4j_database()
        
        # Reset LightRAG storage
        reset_results['lightrag'] = self.reset_lightrag_storage()
        
        # Reset upload directories
        reset_results['uploads'] = self.reset_upload_directories()
        
        # Archive log files
        reset_results['logs'] = self.archive_log_files()
        
        # Reset cache files
        reset_results['cache'] = self.reset_cache_files()
        
        # Summary
        logger.info("=" * 60)
        logger.info("🎯 SYSTEM RESET SUMMARY")
        
        all_success = True
        for component, success in reset_results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            logger.info(f"   {component.upper()}: {status}")
            if not success:
                all_success = False
        
        logger.info(f"📦 Backup directory: {self.backup_dir}")
        logger.info(f"🕐 Reset timestamp: {self.reset_timestamp}")
        
        if all_success:
            logger.info("🎉 COMPLETE SYSTEM RESET SUCCESSFUL!")
            logger.info("✅ System is now clean slate ready for testing")
        else:
            logger.error("❌ SYSTEM RESET PARTIALLY FAILED")
            logger.error("⚠️  Check individual component errors above")
        
        return all_success, reset_results

async def main():
    """Main system reset function."""
    print("🔥 MEMEX SYSTEM RESET")
    print("=" * 50)
    print("This will completely wipe all data:")
    print("- Neo4j database (all nodes & relationships)")
    print("- LightRAG storage (embeddings, entities)")
    print("- Upload directories (all PDFs)")
    print("- Log files (archived)")
    print("- Cache files (deleted)")
    print("=" * 50)
    
    # Confirm reset
    confirm = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ System reset cancelled")
        return False
    
    # Execute reset
    reset_manager = SystemResetManager()
    success, results = await reset_manager.complete_system_reset()
    
    if success:
        print("\n🎉 SYSTEM RESET COMPLETE!")
        print("✅ Clean slate ready for end-to-end testing")
        return True
    else:
        print("\n❌ SYSTEM RESET FAILED")
        print("⚠️  Check logs for specific errors")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n🚀 Ready for end-to-end testing!")
    else:
        print("\n⚠️  System reset incomplete - fix errors before testing")