# Neo4j Setup Guide for RAG-Anything

## Option 1: Docker Setup (Recommended)

### Step 1: Install Docker
If you don't have Docker installed:
- Download from: https://www.docker.com/products/docker-desktop
- Install and start Docker Desktop

### Step 2: Run Neo4j Container
```bash
# Create a Neo4j container with persistent data
docker run \
    --name neo4j-rag \
    -p 7474:7474 -p 7687:7687 \
    -d \
    -v neo4j_data:/data \
    -v neo4j_logs:/logs \
    -v neo4j_import:/var/lib/neo4j/import \
    -v neo4j_plugins:/plugins \
    --env NEO4J_AUTH=neo4j/password123 \
    --env NEO4J_PLUGINS='["apoc"]' \
    neo4j:latest
```

### Step 3: Verify Installation
```bash
# Check if container is running
docker ps | grep neo4j-rag

# View logs
docker logs neo4j-rag
```

### Step 4: Access Neo4j Browser
- Open browser: http://localhost:7474
- Username: `neo4j`
- Password: `password123`

---

## Option 2: Local Installation (macOS)

### Step 1: Install via Homebrew
```bash
# Install Neo4j
brew install neo4j

# Start Neo4j service
brew services start neo4j
```

### Step 2: Configure Neo4j
```bash
# Edit configuration
nano /opt/homebrew/var/neo4j/conf/neo4j.conf

# Add these lines:
dbms.default_listen_address=0.0.0.0
dbms.connector.bolt.listen_address=:7687
dbms.connector.http.listen_address=:7474
```

### Step 3: Set Initial Password
```bash
# Start Neo4j and set password
neo4j-admin set-initial-password password123
```

---

## Option 3: Neo4j Aura (Cloud - Free Tier)

### Step 1: Create Account
- Go to: https://neo4j.com/cloud/aura/
- Sign up for free account
- Create a new database instance

### Step 2: Get Connection Details
- Copy the connection URI (neo4j+s://...)
- Copy username (usually neo4j)
- Copy generated password

---

## Configuration for RAG-Anything

### Update Environment Variables
```bash
# For Docker/Local setup:
export NEO4J_URI=neo4j://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=password123

# For Neo4j Aura:
export NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=your-generated-password
```

### Update .env.rag file
```env
# RAG-Anything Configuration
USE_RAG_ANYTHING=true
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123
RAG_STORAGE_PATH=./rag_storage
RAG_DEBUG=true
FALLBACK_TO_EXISTING=true
USE_GRAPH_CONTEXT=true
```

## Testing the Connection

### Test 1: Basic Connection
```python
from neo4j import GraphDatabase

def test_connection():
    uri = "neo4j://localhost:7687"
    username = "neo4j"
    password = "password123"
    
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        print("✅ Neo4j connection successful!")
        driver.close()
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False

test_connection()
```

### Test 2: RAG Service Health Check
```bash
curl http://localhost:8000/rag-health
```

Should return:
```json
{
  "enabled": true,
  "initialized": true,
  "neo4j_available": true,
  "fallback_enabled": true,
  "storage_path": "./rag_storage"
}
```