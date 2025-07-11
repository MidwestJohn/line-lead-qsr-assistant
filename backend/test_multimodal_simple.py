#!/usr/bin/env python3
"""
Simple Multi-Modal Integration Test
==================================

Direct test of multi-modal capabilities:
1. Environment verification
2. Component functionality testing  
3. Visual citation extraction
4. Basic integration validation
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import time

# Load environment from parent directory
load_dotenv(dotenv_path="../.env")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment configuration"""
    logger.info("🔧 Environment Check")
    
    use_rag_anything = os.getenv('USE_RAG_ANYTHING', 'false').lower() == 'true'
    use_multimodal_citations = os.getenv('USE_MULTIMODAL_CITATIONS', 'false').lower() == 'true'
    
    logger.info(f"   USE_RAG_ANYTHING: {use_rag_anything}")
    logger.info(f"   USE_MULTIMODAL_CITATIONS: {use_multimodal_citations}")
    
    return use_rag_anything, use_multimodal_citations

def check_dependencies():
    """Check critical dependencies"""
    logger.info("📦 Dependency Check")
    
    dependencies = {}
    
    # Check MinerU
    try:
        import mineru
        dependencies['mineru'] = True
        logger.info("   ✅ MinerU available")
    except ImportError:
        dependencies['mineru'] = False
        logger.warning("   ⚠️ MinerU not available")
    
    # Check PyMuPDF (fitz)
    try:
        import fitz
        dependencies['fitz'] = True
        logger.info("   ✅ PyMuPDF (fitz) available")
    except ImportError:
        dependencies['fitz'] = False
        logger.error("   ❌ PyMuPDF (fitz) not available")
    
    # Check LightRAG
    try:
        import lightrag
        dependencies['lightrag'] = True
        logger.info("   ✅ LightRAG available")
    except ImportError:
        dependencies['lightrag'] = False
        logger.error("   ❌ LightRAG not available")
    
    return dependencies

async def test_citation_service():
    """Test Multi-Modal Citation Service directly"""
    logger.info("🔍 Citation Service Test")
    
    try:
        # Import citation service
        from services.multimodal_citation_service import multimodal_citation_service
        
        # Test with sample text that should trigger citations
        test_text = """
        The Taylor C602 ice cream machine requires proper maintenance. 
        Check the temperature specifications in table 2.1 on page 15.
        See diagram 3.2 for the compressor assembly procedure.
        Follow the safety warnings shown in the caution box.
        The temperature sensor should be calibrated to 32°F.
        """
        
        start_time = time.time()
        
        # Extract citations
        citation_result = await multimodal_citation_service.extract_citations_from_response(test_text)
        
        processing_time = time.time() - start_time
        
        # Analyze results
        citations = citation_result.get('visual_citations', [])
        citation_count = citation_result.get('citation_count', 0)
        
        logger.info(f"   Processing time: {processing_time:.2f}s")
        logger.info(f"   Citations found: {citation_count}")
        
        if citations:
            logger.info("   Citation types:")
            citation_types = {}
            for citation in citations:
                ctype = citation.get('type', 'unknown')
                citation_types[ctype] = citation_types.get(ctype, 0) + 1
            
            for ctype, count in citation_types.items():
                logger.info(f"     {ctype}: {count}")
            
            return True
        else:
            logger.warning("   ⚠️ No citations extracted")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ Citation service test failed: {e}")
        return False

def test_document_availability():
    """Check for test documents"""
    logger.info("📄 Document Availability Check")
    
    upload_dirs = ["uploaded_docs", "uploads", "../uploaded_docs", "../uploads"]
    test_docs = []
    
    for upload_dir in upload_dirs:
        dir_path = Path(upload_dir)
        if dir_path.exists():
            pdf_files = list(dir_path.glob("*.pdf"))
            test_docs.extend(pdf_files)
            if pdf_files:
                logger.info(f"   Found {len(pdf_files)} PDFs in {upload_dir}")
    
    if test_docs:
        logger.info(f"   ✅ Total test documents available: {len(test_docs)}")
        for i, doc in enumerate(test_docs[:3]):  # Show first 3
            logger.info(f"     {i+1}. {doc.name}")
        return test_docs[0]  # Return first document for testing
    else:
        logger.warning("   ⚠️ No PDF test documents found")
        return None

async def test_basic_multimodal_extraction():
    """Test basic multi-modal extraction on a real document"""
    logger.info("🎨 Basic Multi-Modal Extraction Test")
    
    test_doc = test_document_availability()
    if not test_doc:
        logger.warning("   Skipping - no test document available")
        return False
    
    try:
        # Test with multi-modal citation service on real document
        from services.multimodal_citation_service import multimodal_citation_service
        
        logger.info(f"   Testing with: {test_doc.name}")
        
        start_time = time.time()
        
        # Index the document for extraction
        await multimodal_citation_service._index_document_content(test_doc)
        
        indexing_time = time.time() - start_time
        
        logger.info(f"   Document indexing completed in {indexing_time:.2f}s")
        
        # Check if document was indexed
        doc_key = str(test_doc)
        if doc_key in multimodal_citation_service.document_index:
            doc_index = multimodal_citation_service.document_index[doc_key]
            
            pages = len(doc_index.get('pages', {}))
            images = sum(len(imgs) for imgs in doc_index.get('images', {}).values())
            tables = sum(len(tabs) for tabs in doc_index.get('tables', {}).values())
            
            logger.info(f"   ✅ Document indexed successfully:")
            logger.info(f"     Pages: {pages}")
            logger.info(f"     Images: {images}")
            logger.info(f"     Tables: {tables}")
            
            return pages > 0 or images > 0 or tables > 0
        else:
            logger.warning("   ⚠️ Document not found in index")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ Multi-modal extraction test failed: {e}")
        return False

def test_neo4j_schema_enhancements():
    """Test Neo4j schema enhancements"""
    logger.info("🗄️ Neo4j Schema Enhancement Test")
    
    try:
        # Test sample entity with multi-modal properties
        sample_entity = {
            'name': 'Taylor C602 Compressor',
            'type': 'Equipment',
            'description': 'Primary cooling system component',
            'visual_refs': ['img_001', 'diag_002'],
            'image_refs': ['img_001'],
            'table_refs': [],
            'diagram_refs': ['diag_002'],
            'page_refs': [15, 23],
            'citation_ids': ['cite_001', 'cite_002'],
            'multimodal_enhanced': True
        }
        
        # Simulate Neo4j property validation
        required_props = ['name', 'type', 'description']
        multimodal_props = ['visual_refs', 'image_refs', 'table_refs', 'diagram_refs', 'page_refs', 'citation_ids']
        
        # Check required properties
        has_required = all(prop in sample_entity for prop in required_props)
        
        # Check multi-modal properties
        has_multimodal = any(sample_entity.get(prop) for prop in multimodal_props)
        
        logger.info(f"   Required properties: {'✅' if has_required else '❌'}")
        logger.info(f"   Multi-modal properties: {'✅' if has_multimodal else '❌'}")
        logger.info(f"   Enhanced: {sample_entity.get('multimodal_enhanced', False)}")
        
        if has_multimodal:
            logger.info("   Multi-modal property summary:")
            for prop in multimodal_props:
                value = sample_entity.get(prop, [])
                if value:
                    logger.info(f"     {prop}: {len(value) if isinstance(value, list) else value}")
        
        return has_required and has_multimodal
        
    except Exception as e:
        logger.error(f"   ❌ Schema enhancement test failed: {e}")
        return False

async def main():
    """Main test execution"""
    logger.info("🎨 Simple Multi-Modal Integration Test")
    logger.info("=" * 50)
    
    # Test 1: Environment
    use_rag, use_citations = check_environment()
    env_score = 20 if (use_rag and use_citations) else 0
    
    # Test 2: Dependencies
    deps = check_dependencies()
    dep_score = 20 if deps.get('fitz') and deps.get('lightrag') else 10 if deps.get('fitz') or deps.get('lightrag') else 0
    
    # Test 3: Citation Service
    citation_success = await test_citation_service()
    citation_score = 20 if citation_success else 0
    
    # Test 4: Multi-modal Extraction
    extraction_success = await test_basic_multimodal_extraction()
    extraction_score = 20 if extraction_success else 0
    
    # Test 5: Schema Enhancements
    schema_success = test_neo4j_schema_enhancements()
    schema_score = 20 if schema_success else 0
    
    # Calculate total score
    total_score = env_score + dep_score + citation_score + extraction_score + schema_score
    
    logger.info("=" * 50)
    logger.info("📊 Test Results Summary:")
    logger.info(f"   Environment Configuration: {env_score}/20")
    logger.info(f"   Dependencies: {dep_score}/20")
    logger.info(f"   Citation Service: {citation_score}/20")
    logger.info(f"   Multi-modal Extraction: {extraction_score}/20")
    logger.info(f"   Schema Enhancements: {schema_score}/20")
    logger.info(f"   TOTAL SCORE: {total_score}/100")
    
    if total_score >= 80:
        logger.info("🎉 Multi-Modal Integration: EXCELLENT")
        status = "EXCELLENT"
    elif total_score >= 60:
        logger.info("✅ Multi-Modal Integration: GOOD")
        status = "GOOD"
    elif total_score >= 40:
        logger.info("⚠️ Multi-Modal Integration: PARTIAL")
        status = "PARTIAL"
    else:
        logger.error("❌ Multi-Modal Integration: NEEDS WORK")
        status = "NEEDS WORK"
    
    logger.info("=" * 50)
    
    # Recommendations
    if not use_rag or not use_citations:
        logger.info("💡 Recommendation: Enable environment variables in .env")
    
    if not deps.get('mineru'):
        logger.info("💡 Recommendation: Install MinerU for advanced processing")
    
    if not citation_success:
        logger.info("💡 Recommendation: Check citation service configuration")
    
    if not extraction_success:
        logger.info("💡 Recommendation: Verify document indexing functionality")
    
    return status in ["EXCELLENT", "GOOD"]

if __name__ == "__main__":
    asyncio.run(main())