#!/usr/bin/env python3
"""
Enhanced Logging System for Complete Pipeline Visibility
Provides comprehensive diagnostic logging throughout upload→Neo4j pipeline:
- Upload endpoint tracking
- LightRAG entity extraction progress
- RAG-Anything multi-modal detection
- Bridge operations monitoring
- Error tracking and recovery
"""

import logging
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import functools

class PipelineLogger:
    """Enhanced logging for complete pipeline visibility."""
    
    def __init__(self, log_file: str = "pipeline_diagnostic.log"):
        self.log_file = log_file
        self.setup_logging()
        self.pipeline_start_time = None
        self.current_stage = None
        self.stage_metrics = {}
        
    def setup_logging(self):
        """Setup comprehensive logging configuration."""
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(name)20s | %(funcName)15s:%(lineno)d | %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        )
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Configure specific loggers
        self.logger = logging.getLogger('PipelineLogger')
        self.upload_logger = logging.getLogger('UploadEndpoint')
        self.lightrag_logger = logging.getLogger('LightRAG')
        self.bridge_logger = logging.getLogger('Neo4jBridge')
        self.multimodal_logger = logging.getLogger('MultiModal')
        
    def start_pipeline(self, file_name: str, file_size: int):
        """Start pipeline tracking."""
        self.pipeline_start_time = time.time()
        self.current_stage = "UPLOAD"
        self.stage_metrics = {
            'file_name': file_name,
            'file_size': file_size,
            'start_time': datetime.now().isoformat(),
            'stages': {}
        }
        
        self.logger.info("🚀 PIPELINE START")
        self.logger.info("=" * 60)
        self.logger.info(f"📄 File: {file_name}")
        self.logger.info(f"📊 Size: {file_size:,} bytes")
        
    def log_stage_start(self, stage_name: str, details: Dict[str, Any] = None):
        """Log the start of a pipeline stage."""
        self.current_stage = stage_name
        stage_start_time = time.time()
        
        self.stage_metrics['stages'][stage_name] = {
            'start_time': datetime.now().isoformat(),
            'start_timestamp': stage_start_time,
            'details': details or {}
        }
        
        self.logger.info(f"🔄 STAGE START: {stage_name}")
        if details:
            for key, value in details.items():
                self.logger.info(f"   {key}: {value}")
                
    def log_stage_progress(self, stage_name: str, progress: Dict[str, Any]):
        """Log progress within a stage."""
        if stage_name in self.stage_metrics['stages']:
            if 'progress' not in self.stage_metrics['stages'][stage_name]:
                self.stage_metrics['stages'][stage_name]['progress'] = []
            
            progress_entry = {
                'timestamp': datetime.now().isoformat(),
                'data': progress
            }
            self.stage_metrics['stages'][stage_name]['progress'].append(progress_entry)
        
        self.logger.info(f"📊 {stage_name} PROGRESS:")
        for key, value in progress.items():
            self.logger.info(f"   {key}: {value}")
            
    def log_stage_complete(self, stage_name: str, results: Dict[str, Any] = None):
        """Log the completion of a pipeline stage."""
        if stage_name in self.stage_metrics['stages']:
            stage_info = self.stage_metrics['stages'][stage_name]
            end_time = time.time()
            duration = end_time - stage_info['start_timestamp']
            
            stage_info.update({
                'end_time': datetime.now().isoformat(),
                'duration_seconds': duration,
                'results': results or {}
            })
            
            self.logger.info(f"✅ STAGE COMPLETE: {stage_name}")
            self.logger.info(f"   Duration: {duration:.2f} seconds")
            if results:
                for key, value in results.items():
                    self.logger.info(f"   {key}: {value}")
    
    def log_error(self, stage_name: str, error: Exception, context: Dict[str, Any] = None):
        """Log detailed error information."""
        error_details = {
            'stage': stage_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context or {},
            'traceback': traceback.format_exc()
        }
        
        if stage_name in self.stage_metrics['stages']:
            self.stage_metrics['stages'][stage_name]['error'] = error_details
        
        self.logger.error(f"❌ ERROR in {stage_name}: {error}")
        if context:
            for key, value in context.items():
                self.logger.error(f"   {key}: {value}")
        
        # Log full traceback to file only
        file_logger = logging.getLogger('ErrorTraceback')
        file_logger.debug(f"Full traceback for {stage_name}:")
        file_logger.debug(traceback.format_exc())
        
    def complete_pipeline(self, success: bool, final_results: Dict[str, Any] = None):
        """Complete pipeline tracking."""
        if self.pipeline_start_time:
            total_duration = time.time() - self.pipeline_start_time
            
            self.stage_metrics.update({
                'end_time': datetime.now().isoformat(),
                'total_duration_seconds': total_duration,
                'success': success,
                'final_results': final_results or {}
            })
            
            self.logger.info("=" * 60)
            if success:
                self.logger.info("🎉 PIPELINE COMPLETE - SUCCESS")
            else:
                self.logger.error("❌ PIPELINE COMPLETE - FAILED")
            
            self.logger.info(f"⏱️  Total Duration: {total_duration:.2f} seconds")
            
            if final_results:
                for key, value in final_results.items():
                    self.logger.info(f"📊 {key}: {value}")
                    
            # Save metrics to file
            self.save_pipeline_metrics()
            
    def save_pipeline_metrics(self):
        """Save detailed pipeline metrics to JSON file."""
        metrics_file = f"pipeline_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(metrics_file, 'w') as f:
                json.dump(self.stage_metrics, f, indent=2)
            
            self.logger.info(f"📊 Pipeline metrics saved to {metrics_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save pipeline metrics: {e}")

# Global pipeline logger instance
pipeline_logger = PipelineLogger()

def log_pipeline_stage(stage_name: str):
    """Decorator to automatically log pipeline stages."""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            pipeline_logger.log_stage_start(stage_name, {'function': func.__name__})
            
            try:
                result = await func(*args, **kwargs)
                pipeline_logger.log_stage_complete(stage_name, {'success': True})
                return result
            except Exception as e:
                pipeline_logger.log_error(stage_name, e, {
                    'function': func.__name__,
                    'args': str(args)[:200],
                    'kwargs': str(kwargs)[:200]
                })
                raise
                
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            pipeline_logger.log_stage_start(stage_name, {'function': func.__name__})
            
            try:
                result = func(*args, **kwargs)
                pipeline_logger.log_stage_complete(stage_name, {'success': True})
                return result
            except Exception as e:
                pipeline_logger.log_error(stage_name, e, {
                    'function': func.__name__,
                    'args': str(args)[:200],
                    'kwargs': str(kwargs)[:200]
                })
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Upload endpoint logging
class UploadEndpointLogger:
    """Specialized logging for upload endpoints."""
    
    def __init__(self):
        self.logger = logging.getLogger('UploadEndpoint')
        
    def log_file_received(self, file_name: str, file_size: int, content_type: str):
        """Log file receipt."""
        self.logger.info(f"📄 FILE RECEIVED: {file_name}")
        self.logger.info(f"   Size: {file_size:,} bytes")
        self.logger.info(f"   Type: {content_type}")
        
        pipeline_logger.start_pipeline(file_name, file_size)
        
    def log_file_validation(self, file_name: str, is_valid: bool, validation_details: Dict[str, Any]):
        """Log file validation results."""
        if is_valid:
            self.logger.info(f"✅ FILE VALIDATION PASSED: {file_name}")
        else:
            self.logger.error(f"❌ FILE VALIDATION FAILED: {file_name}")
            
        for key, value in validation_details.items():
            self.logger.info(f"   {key}: {value}")
            
    def log_processing_start(self, file_name: str, processing_options: Dict[str, Any]):
        """Log processing start."""
        self.logger.info(f"🔄 PROCESSING START: {file_name}")
        for key, value in processing_options.items():
            self.logger.info(f"   {key}: {value}")

# LightRAG logging
class LightRAGLogger:
    """Specialized logging for LightRAG operations."""
    
    def __init__(self):
        self.logger = logging.getLogger('LightRAG')
        
    def log_initialization(self, config: Dict[str, Any]):
        """Log LightRAG initialization."""
        self.logger.info("🔧 LIGHTRAG INITIALIZATION")
        for key, value in config.items():
            self.logger.info(f"   {key}: {value}")
            
    def log_document_insertion(self, content_length: int, chunk_count: int):
        """Log document insertion start."""
        self.logger.info(f"📄 DOCUMENT INSERTION START")
        self.logger.info(f"   Content length: {content_length:,} characters")
        self.logger.info(f"   Estimated chunks: {chunk_count}")
        
    def log_entity_extraction_progress(self, entities_found: int, relationships_found: int):
        """Log entity extraction progress."""
        self.logger.info(f"🔍 ENTITY EXTRACTION PROGRESS")
        self.logger.info(f"   Entities found: {entities_found}")
        self.logger.info(f"   Relationships found: {relationships_found}")
        
        pipeline_logger.log_stage_progress('ENTITY_EXTRACTION', {
            'entities_found': entities_found,
            'relationships_found': relationships_found
        })
        
    def log_extraction_complete(self, final_entities: int, final_relationships: int):
        """Log extraction completion."""
        self.logger.info(f"✅ ENTITY EXTRACTION COMPLETE")
        self.logger.info(f"   Final entities: {final_entities}")
        self.logger.info(f"   Final relationships: {final_relationships}")

# Multi-modal logging
class MultiModalLogger:
    """Specialized logging for multi-modal content processing."""
    
    def __init__(self):
        self.logger = logging.getLogger('MultiModal')
        
    def log_content_analysis(self, content_types: Dict[str, int]):
        """Log multi-modal content analysis."""
        self.logger.info("🖼️  MULTI-MODAL CONTENT ANALYSIS")
        for content_type, count in content_types.items():
            self.logger.info(f"   {content_type}: {count}")
            
    def log_image_extraction(self, image_count: int, total_size: int):
        """Log image extraction."""
        self.logger.info(f"📸 IMAGE EXTRACTION: {image_count} images, {total_size:,} bytes")
        
    def log_table_extraction(self, table_count: int, row_count: int):
        """Log table extraction."""
        self.logger.info(f"📋 TABLE EXTRACTION: {table_count} tables, {row_count} rows")

# Bridge logging
class Neo4jBridgeLogger:
    """Specialized logging for Neo4j bridge operations."""
    
    def __init__(self):
        self.logger = logging.getLogger('Neo4jBridge')
        
    def log_bridge_start(self, entity_count: int, relationship_count: int):
        """Log bridge operation start."""
        self.logger.info(f"🌉 NEO4J BRIDGE START")
        self.logger.info(f"   Entities to process: {entity_count}")
        self.logger.info(f"   Relationships to process: {relationship_count}")
        
    def log_batch_processing(self, batch_num: int, batch_size: int, total_batches: int):
        """Log batch processing progress."""
        self.logger.info(f"📦 BATCH {batch_num}/{total_batches}: {batch_size} items")
        
        pipeline_logger.log_stage_progress('NEO4J_BRIDGE', {
            'batch_num': batch_num,
            'total_batches': total_batches,
            'batch_size': batch_size,
            'progress_percent': (batch_num / total_batches) * 100
        })
        
    def log_neo4j_connection(self, connection_success: bool, retry_count: int = 0):
        """Log Neo4j connection attempts."""
        if connection_success:
            self.logger.info(f"✅ NEO4J CONNECTION SUCCESS")
        else:
            self.logger.error(f"❌ NEO4J CONNECTION FAILED (attempt {retry_count + 1})")
            
    def log_bridge_complete(self, entities_created: int, relationships_created: int):
        """Log bridge completion."""
        self.logger.info(f"✅ NEO4J BRIDGE COMPLETE")
        self.logger.info(f"   Entities created: {entities_created}")
        self.logger.info(f"   Relationships created: {relationships_created}")

# Initialize logger instances
upload_logger = UploadEndpointLogger()
lightrag_logger = LightRAGLogger()
multimodal_logger = MultiModalLogger()
bridge_logger = Neo4jBridgeLogger()

# Export logging functions
__all__ = [
    'pipeline_logger',
    'upload_logger', 
    'lightrag_logger',
    'multimodal_logger',
    'bridge_logger',
    'log_pipeline_stage'
]