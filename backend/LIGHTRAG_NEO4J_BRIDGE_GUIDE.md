# LightRAG → Neo4j Bridge Guide

## Overview

This guide provides a complete solution for reliably transferring LightRAG-extracted knowledge graphs to Neo4j, bypassing the async context management bugs in the LightRAG library.

## 🎯 Problem Solved

**Issue**: LightRAG direct Neo4j integration fails with async context management errors
**Solution**: Robust manual bridge with enterprise-grade reliability features

## 🔧 Components

### 1. **LightRAG Data Extractor** (`extract_lightrag_data.py`)
- Finds and extracts data from various LightRAG storage formats
- Handles JSON files, graph storage, and multiple directory structures
- Normalizes data to standard format
- Removes duplicates

### 2. **Neo4j Bridge** (`lightrag_neo4j_bridge.py`)
- Batch processing with configurable batch size
- Exponential backoff retries (3 attempts)
- Transaction rollback on failure
- Deduplication logic
- Progress tracking with detailed logs
- Resume from checkpoint capability
- Connection drop handling

### 3. **Test Suite** (`test_bridge.py`)
- Comprehensive testing with sample QSR data
- Performance benchmarking
- Error scenario testing

## 🚀 Quick Start

### Step 1: Extract LightRAG Data
```bash
# Extract from default storage
python extract_lightrag_data.py

# Extract from specific directory
python extract_lightrag_data.py --storage ./rag_storage_custom

# Custom output files
python extract_lightrag_data.py --entities my_entities.json --relationships my_relationships.json
```

### Step 2: Bridge to Neo4j
```bash
# Basic bridge operation
python lightrag_neo4j_bridge.py

# Custom files and batch size
python lightrag_neo4j_bridge.py --entities my_entities.json --relationships my_relationships.json --batch-size 1000

# Resume from checkpoint
python lightrag_neo4j_bridge.py --checkpoint my_checkpoint.json

# Retry failed items only
python lightrag_neo4j_bridge.py --retry-failed
```

## 🔍 Advanced Usage

### Configuration Options

**Batch Size**: Adjust based on your data size and network latency
```bash
# Small datasets (< 1000 items)
python lightrag_neo4j_bridge.py --batch-size 100

# Large datasets (> 10000 items)
python lightrag_neo4j_bridge.py --batch-size 1000
```

**Checkpoint Management**: 
```bash
# Use custom checkpoint file
python lightrag_neo4j_bridge.py --checkpoint production_checkpoint.json

# Resume interrupted processing
python lightrag_neo4j_bridge.py --checkpoint production_checkpoint.json
```

### Python API Usage

```python
from lightrag_neo4j_bridge import LightRAGNeo4jBridge

# Create bridge instance
bridge = LightRAGNeo4jBridge(
    entities_file="entities.json",
    relationships_file="relationships.json",
    batch_size=500,
    checkpoint_file="checkpoint.json"
)

# Run the bridge
result = bridge.run_bridge()

if result["success"]:
    print(f"✅ Processed {result['entities_processed']} entities")
    print(f"✅ Processed {result['relationships_processed']} relationships")
else:
    print(f"❌ Error: {result['error']}")

# Get detailed progress
summary = bridge.get_progress_summary()
print(f"Processing rate: {summary['entities']['rate_per_second']:.2f} entities/sec")
```

## 📊 Features

### Reliability Features
- **Exponential Backoff**: Handles transient network errors
- **Transaction Rollback**: Ensures data consistency
- **Batch Processing**: Optimizes performance and memory usage
- **Checkpoint Resume**: Continue from where you left off
- **Deduplication**: Prevents duplicate nodes and relationships

### Monitoring & Observability
- **Detailed Logging**: Track every operation
- **Progress Tracking**: Real-time progress updates
- **Performance Metrics**: Processing rates and timings
- **Error Reporting**: Detailed error information

### Data Handling
- **Flexible Input**: Handles various LightRAG formats
- **Smart Normalization**: Converts to standard Neo4j format
- **Dynamic Labels**: Creates appropriate node labels
- **Property Preservation**: Maintains all original data

## 🏗️ Architecture

```
LightRAG Storage → Extract → Normalize → Bridge → Neo4j
     │               │         │          │        │
     │               │         │          │        └─ Nodes & Relationships
     │               │         │          └─ Batch Processing
     │               │         └─ JSON Format
     │               └─ Multiple Formats
     └─ Various Storage Types
```

## 🔧 Configuration

### Environment Variables (.env.rag)
```bash
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

### Neo4j Setup
1. **Neo4j Aura** (Recommended)
   - Cloud-hosted, managed Neo4j instance
   - SSL by default (neo4j+s:// URI)
   - Automatic backups and scaling

2. **Self-hosted Neo4j**
   - Update URI to neo4j://localhost:7687
   - Ensure authentication is configured

## 🧪 Testing

### Run Test Suite
```bash
# Basic test with sample data
python test_bridge.py

# Test with existing data
python lightrag_neo4j_bridge.py --entities test_entities.json --relationships test_relationships.json
```

### Verify Results
```python
from services.neo4j_service import neo4j_service

# Check node count
if neo4j_service.connect():
    nodes = neo4j_service.get_node_count()
    relationships = neo4j_service.get_relationship_count()
    print(f"Graph has {nodes} nodes and {relationships} relationships")
```

## 📈 Performance Optimization

### Batch Size Guidelines
| Dataset Size | Recommended Batch Size | Memory Usage |
|-------------|------------------------|--------------|
| < 1,000     | 100                   | Low          |
| 1,000-10,000| 500                   | Medium       |
| 10,000+     | 1,000                 | High         |

### Network Optimization
- Use Neo4j Aura for better network performance
- Adjust connection pool settings for high-volume loads
- Consider running bridge from same cloud region as Neo4j

## 🛠️ Troubleshooting

### Common Issues

**1. Connection Timeout**
```bash
# Increase timeout in bridge configuration
# Edit lightrag_neo4j_bridge.py, line ~79
connection_acquisition_timeout=120  # Increase from 60
```

**2. Memory Issues with Large Datasets**
```bash
# Reduce batch size
python lightrag_neo4j_bridge.py --batch-size 100
```

**3. Duplicate Data**
```bash
# Bridge automatically deduplicates, but you can verify:
python -c "
from lightrag_neo4j_bridge import LightRAGNeo4jBridge
bridge = LightRAGNeo4jBridge()
# Check progress for duplicate counts
"
```

**4. Partial Processing**
```bash
# Resume from checkpoint
python lightrag_neo4j_bridge.py --checkpoint existing_checkpoint.json
```

### Debugging

**Enable Debug Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check Neo4j Connectivity**:
```python
from services.neo4j_service import neo4j_service
status = neo4j_service.get_health_status()
print(status)
```

## 🎉 Success Metrics

### Expected Results
- **Processing Rate**: 5-50 entities/second (depends on complexity)
- **Success Rate**: 99%+ with retry logic
- **Memory Usage**: Minimal (batch processing)
- **Resumability**: 100% with checkpoints

### Verification
After successful bridge operation:
```bash
# Check graph statistics
python -c "
from services.neo4j_service import neo4j_service
if neo4j_service.connect():
    result = neo4j_service.execute_query('MATCH (n) RETURN labels(n)[0] as label, count(n) as count')
    print('Node distribution:')
    for record in result['records']:
        print(f'  {record[\"label\"]}: {record[\"count\"]}')
"
```

## 🔄 Production Workflow

### 1. Data Preparation
```bash
# Extract from LightRAG
python extract_lightrag_data.py --storage ./production_rag_storage

# Verify extraction
ls -la extracted_*.json
```

### 2. Bridge to Neo4j
```bash
# Production bridge with monitoring
python lightrag_neo4j_bridge.py \
  --entities extracted_entities.json \
  --relationships extracted_relationships.json \
  --batch-size 1000 \
  --checkpoint production_checkpoint.json \
  > bridge_production.log 2>&1
```

### 3. Verification
```bash
# Check results
tail -f bridge_production.log

# Verify in Neo4j
python -c "
from services.neo4j_service import neo4j_service
if neo4j_service.connect():
    stats = neo4j_service.count_nodes_and_relationships()
    print(f'Final graph: {stats[\"nodes\"]} nodes, {stats[\"relationships\"]} relationships')
"
```

## 📚 Integration with QSR MVP

The bridge integrates seamlessly with the Line Lead QSR MVP:

1. **Document Processing**: Process QSR manuals with any working GraphRAG tool
2. **Data Extraction**: Use the extractor to prepare data
3. **Bridge to Neo4j**: Use the bridge for reliable Neo4j population
4. **Frontend Access**: Existing frontend can query the populated graph

This approach gives you the reliability of enterprise-grade data pipeline while maintaining the flexibility of the GraphRAG ecosystem.

---

**Generated with [Memex](https://memex.tech)**