# Data Persistence Guide

This document explains how data persistence works for both the database and Elasticsearch.

## Database (SQLite) - ✅ PERSISTENT

### Current Setup
- **Location**: `search-ui/backend/app.db`
- **Type**: SQLite database file
- **Persistence**: ✅ **YES - Fully Persistent**

The database file (`app.db`) is stored on disk and persists across:
- Server restarts
- Application restarts
- System reboots

The file is created automatically when you first run the application or migration script.

### What's Stored
- Companies
- Persons
- Notes

### Backup Recommendations
- The `app.db` file can be backed up by simply copying it
- Consider adding it to your backup strategy
- Location: `search-ui/backend/app.db`

---

## Elasticsearch - ⚠️ NOT PERSISTENT (Current Setup)

### Current Setup
The Docker command in the documentation does **NOT** include a volume mount:

```bash
docker run -d -p 9200:9200 -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "xpack.security.enrollment.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0
```

**This means**: 
- ❌ Data is **NOT persistent** across container restarts
- ❌ If you remove the container, all indexed documents are lost
- ❌ You'll need to re-index documents after restarting the container

### What's Stored in Elasticsearch
- **Documents only** (PDF/DOCX files that have been uploaded and indexed)
- Companies, persons, and notes are NOT indexed (they're in the database)

---

## Making Elasticsearch Persistent

### Option 1: Add Volume Mount (Recommended)

Stop the current container and start with a volume:

```powershell
# Stop and remove existing container
docker stop <container_id>
docker rm <container_id>

# Start with persistent volume
docker run -d -p 9200:9200 -p 9300:9300 `
  -e "discovery.type=single-node" `
  -e "xpack.security.enabled=false" `
  -e "xpack.security.enrollment.enabled=false" `
  -v elasticsearch-data:/usr/share/elasticsearch/data `
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0
```

This creates a Docker volume named `elasticsearch-data` that persists even if the container is removed.

### Option 2: Bind Mount to Local Directory

```powershell
# Create directory for Elasticsearch data
mkdir C:\elasticsearch-data

# Start with bind mount
docker run -d -p 9200:9200 -p 9300:9300 `
  -e "discovery.type=single-node" `
  -e "xpack.security.enabled=false" `
  -e "xpack.security.enrollment.enabled=false" `
  -v C:\elasticsearch-data:/usr/share/elasticsearch/data `
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0
```

**Note**: On Windows, you may need to adjust permissions or use WSL2 paths.

### Option 3: Use Docker Compose (Best for Production)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - xpack.security.enrollment.enabled=false
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

volumes:
  elasticsearch-data:
```

Then run:
```bash
docker-compose up -d
```

---

## Data Recovery

### If Elasticsearch Data is Lost

Since only documents are indexed in Elasticsearch, you can recover by:

1. **Re-uploading documents**: Users can re-upload their PDF/DOCX files
2. **Automated re-indexing**: You could implement a script to re-index all uploaded files from the `uploads/` directory

### If Database is Lost

1. **Run migration again**: 
   ```bash
   python migrate_json_to_db.py
   ```
2. **Restore from backup**: If you have a backup of `app.db`, restore it

---

## Recommendations

1. **For Development**: 
   - Database: Already persistent ✅
   - Elasticsearch: Add volume mount (Option 1) if you want to keep indexed documents

2. **For Production**:
   - Database: Add regular backups of `app.db`
   - Elasticsearch: Use Docker Compose with named volumes (Option 3)
   - Consider using managed Elasticsearch service (Elastic Cloud, AWS OpenSearch, etc.)

3. **Backup Strategy**:
   - Database: Copy `app.db` regularly
   - Elasticsearch: Use snapshot/restore API or backup the volume
   - Uploaded files: Backup `search-ui/backend/uploads/` directory

---

## Checking Current Status

### Check if database exists:
```bash
ls search-ui/backend/app.db
```

### Check Elasticsearch indices:
```powershell
Invoke-RestMethod -Method GET -Uri "http://localhost:9200/_cat/indices?v"
```

### Check Docker volumes (if using volumes):
```bash
docker volume ls
docker volume inspect elasticsearch-data
```

