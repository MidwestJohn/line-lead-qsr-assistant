
# Enterprise Bridge Test Suite Report

## Executive Summary
- **Total Tests**: 7
- **Passed**: 1
- **Failed**: 6
- **Success Rate**: 14.3%

## Test Results Details

### ✅ Test Data Preparation
**Status**: passed

### ❌ Qsr Entity Detection
**Status**: failed
**Errors**: cannot import name 'QSREntityExtractor' from 'backend.services.qsr_entity_extractor' (/Users/johninniger/Workspace/line_lead_qsr_mvp/backend/services/qsr_entity_extractor.py)

### ❌ Multimodal Embedding
**Status**: failed
**Errors**: cannot import name 'get_env_value' from 'lightrag.utils' (/Users/johninniger/Workspace/line_lead_qsr_mvp/.venv/lib/python3.10/site-packages/lightrag/utils.py)

### ❌ Enterprise Bridge
**Status**: failed
**Errors**: 'AutomaticBridgeService' object has no attribute 'transfer_data'

### ❌ Neo4J Relationships
**Status**: failed
**Errors**: Neo4jRelationshipGenerator.__init__() missing 1 required positional argument: 'neo4j_service'

### ❌ End To End
**Status**: failed
**Errors**: cannot import name 'TrueRAGService' from 'backend.services.true_rag_service' (/Users/johninniger/Workspace/line_lead_qsr_mvp/backend/services/true_rag_service.py)

### ❌ Knowledge Quality
**Status**: failed
**Errors**: cannot import name 'DataIntegrityVerification' from 'backend.data_integrity_verification' (/Users/johninniger/Workspace/line_lead_qsr_mvp/backend/data_integrity_verification.py)

