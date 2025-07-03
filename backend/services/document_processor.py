import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import asyncio
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ProcessedContent:
    text_chunks: List[str]
    images: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_method: str

class DocumentProcessor:
    def __init__(self):
        self.use_rag_anything = os.getenv('USE_RAG_ANYTHING', 'false').lower() == 'true'
        self.mineru_available = self._check_mineru()
        
    def _check_mineru(self) -> bool:
        """Check if MinerU is available for advanced processing."""
        try:
            import mineru
            return True
        except ImportError:
            return False
    
    async def process_pdf_basic(self, file_path: str) -> ProcessedContent:
        """Process PDF using existing PyPDF2 method."""
        from backend.main import extract_text_from_pdf  # Use existing function
        
        text_content = extract_text_from_pdf(file_path)
        
        # Use existing chunking logic
        chunks = self._chunk_text_existing_method(text_content)
        
        return ProcessedContent(
            text_chunks=chunks,
            images=[],
            tables=[],
            metadata={"source": "pypdf2", "file_path": file_path},
            processing_method="basic"
        )
    
    def _chunk_text_existing_method(self, text: str) -> List[str]:
        """Use existing text chunking approach."""
        # Copy exact logic from main.py chunk_text function
        chunk_size = 512
        overlap = 50
        chunks = []
        
        words = text.split()
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    async def process_pdf_advanced(self, file_path: str) -> ProcessedContent:
        """Process PDF using RAG-Anything + MinerU for multi-modal extraction."""
        if not self.mineru_available:
            logger.warning("MinerU not available, falling back to basic processing")
            return await self.process_pdf_basic(file_path)
        
        try:
            # Use MinerU for document parsing
            import mineru
            from raganything import RAGAnything
            
            # Initialize RAG-Anything document processor
            rag_anything = RAGAnything()
            
            # Process document through MinerU pipeline
            processed_doc = await rag_anything.process_document(file_path)
            
            return ProcessedContent(
                text_chunks=processed_doc.get('text_chunks', []),
                images=processed_doc.get('images', []),
                tables=processed_doc.get('tables', []),
                metadata={
                    "source": "mineru",
                    "file_path": file_path,
                    "processing_time": processed_doc.get('processing_time'),
                    "elements_found": {
                        "text_blocks": len(processed_doc.get('text_chunks', [])),
                        "images": len(processed_doc.get('images', [])),
                        "tables": len(processed_doc.get('tables', []))
                    }
                },
                processing_method="advanced"
            )
            
        except Exception as e:
            logger.error(f"Advanced processing failed: {e}")
            return await self.process_pdf_basic(file_path)
    
    async def process_document(self, file_path: str) -> ProcessedContent:
        """Main document processing entry point."""
        if self.use_rag_anything:
            return await self.process_pdf_advanced(file_path)
        else:
            return await self.process_pdf_basic(file_path)
    
    def save_processed_content(self, content: ProcessedContent, output_dir: str = "processed_docs") -> str:
        """Save processed content to structured format."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Create unique filename based on source
        base_name = Path(content.metadata["file_path"]).stem
        output_file = os.path.join(output_dir, f"{base_name}_processed.json")
        
        # Convert to serializable format
        data = asdict(content)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Processed content saved to {output_file}")
        return output_file

# Global instance
document_processor = DocumentProcessor()