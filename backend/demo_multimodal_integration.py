#!/usr/bin/env python3
"""
Multi-Modal Integration Demo
===========================

Quick demonstration of the complete multi-modal integration:
- Document processing with visual content extraction
- Entity enhancement with visual references
- Neo4j population with visual citation nodes
"""

import asyncio
import logging
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv(dotenv_path="../.env")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def demo_multimodal_integration():
    """Demonstrate multi-modal integration capabilities"""
    
    logger.info("🎨 Multi-Modal Integration Demo")
    logger.info("=" * 50)
    
    # Step 1: Show configuration
    import os
    logger.info("📋 Configuration:")
    logger.info(f"   RAG-Anything: {os.getenv('USE_RAG_ANYTHING', 'false')}")
    logger.info(f"   Multi-Modal Citations: {os.getenv('USE_MULTIMODAL_CITATIONS', 'false')}")
    
    # Step 2: Import components
    logger.info("📦 Loading Multi-Modal Components...")
    
    try:
        from services.multimodal_bridge_processor import multimodal_bridge_processor
        from services.multimodal_citation_service import multimodal_citation_service
        logger.info("✅ Multi-modal components loaded")
    except Exception as e:
        logger.error(f"❌ Component loading failed: {e}")
        return
    
    # Step 3: Find test document
    logger.info("📄 Finding test document...")
    
    test_docs = []
    for upload_dir in ["uploaded_docs", "../uploaded_docs"]:
        dir_path = Path(upload_dir)
        if dir_path.exists():
            test_docs.extend(list(dir_path.glob("*.pdf")))
    
    if not test_docs:
        logger.error("❌ No test documents found")
        return
    
    test_doc = test_docs[0]
    logger.info(f"✅ Using: {test_doc.name}")
    
    # Step 4: Citation Service Demo
    logger.info("🔍 Citation Service Demo...")
    
    sample_text = """
    The Taylor C602 ice cream machine requires temperature monitoring.
    Check table 2.1 for specifications and see diagram 3.2 for assembly.
    Safety warning: Always follow proper cleaning procedures.
    Set temperature to 32°F as shown in the manual.
    """
    
    start_time = time.time()
    citations = await multimodal_citation_service.extract_citations_from_response(sample_text)
    citation_time = time.time() - start_time
    
    logger.info(f"✅ Citations extracted in {citation_time:.2f}s")
    logger.info(f"   Found {citations['citation_count']} visual citations:")
    
    for citation in citations['visual_citations'][:3]:  # Show first 3
        logger.info(f"     {citation['type']}: {citation['reference']}")
    
    # Step 5: Document Processing Demo
    logger.info("🎨 Document Processing Demo...")
    
    try:
        start_time = time.time()
        
        result = await multimodal_bridge_processor.process_document_with_multimodal(
            str(test_doc),
            test_doc.name
        )
        
        processing_time = time.time() - start_time
        stats = result.statistics
        
        logger.info(f"✅ Document processed in {processing_time:.2f}s")
        logger.info(f"   Method: {result.processing_method}")
        logger.info(f"   Entities: {stats['entities_extracted']}")
        logger.info(f"   Visual citations: {stats['visual_citations']}")
        logger.info(f"   Images: {stats['images_found']}")
        logger.info(f"   Tables: {stats['tables_found']}")
        logger.info(f"   Enhanced entities: {stats['visual_enhancements']}")
        
        # Show sample enhanced entity
        enhanced_entities = [e for e in result.entities if e.get('multimodal_enhanced')]
        if enhanced_entities:
            sample_entity = enhanced_entities[0]
            logger.info("📋 Sample Enhanced Entity:")
            logger.info(f"     Name: {sample_entity.get('name', 'Unknown')}")
            logger.info(f"     Visual refs: {len(sample_entity.get('visual_refs', []))}")
            logger.info(f"     Image refs: {len(sample_entity.get('image_refs', []))}")
            logger.info(f"     Page refs: {sample_entity.get('page_refs', [])}")
        
    except Exception as e:
        logger.error(f"❌ Document processing failed: {e}")
        return
    
    # Step 6: Statistics Summary
    logger.info("📊 Integration Summary:")
    processor_stats = multimodal_bridge_processor.get_processing_statistics()
    
    logger.info(f"   Documents processed: {processor_stats['documents_processed']}")
    logger.info(f"   Visual citations extracted: {processor_stats['visual_citations_extracted']}")
    logger.info(f"   Enhanced entities: {processor_stats['enhanced_entities']}")
    logger.info(f"   Multi-modal enabled: {processor_stats['multimodal_enabled']}")
    
    # Step 7: Success Assessment
    logger.info("=" * 50)
    
    success_indicators = [
        ("Configuration valid", os.getenv('USE_RAG_ANYTHING') == 'true'),
        ("Citations generated", citations['citation_count'] > 0),
        ("Document processed", stats['entities_extracted'] > 0),
        ("Visual content found", stats['visual_citations'] > 0 or stats['images_found'] > 0),
        ("Entities enhanced", stats['visual_enhancements'] > 0),
        ("Processing efficient", processing_time < 60)
    ]
    
    passed = sum(1 for _, result in success_indicators if result)
    total = len(success_indicators)
    
    logger.info("✅ Success Indicators:")
    for indicator, result in success_indicators:
        status = "✅" if result else "❌"
        logger.info(f"   {status} {indicator}")
    
    success_rate = (passed / total) * 100
    logger.info(f"📊 Success Rate: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate >= 80:
        logger.info("🎉 MULTI-MODAL INTEGRATION: FULLY OPERATIONAL")
        logger.info("   Ready for production use!")
    elif success_rate >= 60:
        logger.info("✅ MULTI-MODAL INTEGRATION: MOSTLY OPERATIONAL")
        logger.info("   Minor optimizations recommended")
    else:
        logger.info("⚠️ MULTI-MODAL INTEGRATION: PARTIAL OPERATION")
        logger.info("   Review configuration and dependencies")
    
    logger.info("=" * 50)
    logger.info("🎨 Multi-Modal Integration Demo Complete")

if __name__ == "__main__":
    asyncio.run(demo_multimodal_integration())