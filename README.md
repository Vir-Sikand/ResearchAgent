# Postgres+pgvector + MindsDB Setup

This setup provides a complete environment with Postgres+pgvector for vector storage and MindsDB for AI/ML capabilities.

## Quick Start

### 1. Start the services

```bash
docker compose --env-file ./.env up -d
docker compose ps
```

### 2. Access MindsDB GUI

Open **[http://127.0.0.1:47334](http://127.0.0.1:47334)** for the MindsDB GUI.

- Default username: `mindsdb`
- Default password: (empty)

### 3. Connect via MySQL CLI (alternative)

```bash
mysql -h 127.0.0.1 --port 47335 -u mindsdb
```

### 4. Verify pgvector extension

```bash
docker exec -it pgvector_db psql -U kb_user -d kb -c "\dx"
```

You should see `vector` in the extensions list.

## Services

### Postgres+pgvector
- **Container**: `pgvector_db`
- **Port**: 5432
- **Database**: `kb`
- **User**: `kb_user`
- **Password**: `kb_pass_123`

### MindsDB
- **Container**: `mindsdb`
- **HTTP GUI/API**: 47334
- **MySQL-compatible SQL API**: 47335

## Next Steps: Wire MindsDB → Postgres

From the MindsDB SQL editor (GUI at 47334) or MySQL client to port 47335:

```sql
-- Create a connection to your pgvector Postgres
CREATE DATABASE org_pg
WITH ENGINE = 'pgvector',
PARAMETERS = {
  "host": "postgres",
  "port": 5432,
  "database": "kb",
  "user": "kb_user",
  "password": "kb_pass_123",
  "distance": "cosine"
};
```

## Create Knowledge Base

### Option A: Default storage (Chroma)

```sql
CREATE KNOWLEDGE_BASE org_kb
USING
  embedding_model = {
    "provider": "openai",
    "model_name": "text-embedding-3-small",
    "api_key": from_env('OPENAI_API_KEY')
  },
  reranking_model = false;
```

### Option B: Store embeddings in pgvector

```sql
CREATE KNOWLEDGE_BASE org_kb_pg
USING
  embedding_model = {
    "provider": "openai",
    "model_name": "text-embedding-3-small",
    "api_key": from_env('OPENAI_API_KEY')
  },
  reranking_model = false,
  storage = org_pg.storage_table;
```

## Test the Knowledge Base

```sql
-- Insert test data
INSERT INTO org_kb (content) VALUES ('Our PRD requires an agent router to choose KB vs research.');
INSERT INTO org_kb_pg (content) VALUES ('ThinkGPT compresses long research notes into memory.');

-- Semantic search
SELECT * FROM org_kb WHERE content = 'agent routing research vs KB';
SELECT * FROM org_kb_pg WHERE content = 'compression of research notes';
```

## Troubleshooting

- **GUI not loading?** Check container logs: `docker logs mindsdb`
- **MySQL CLI connection issues?** Always use `-h 127.0.0.1 --port 47335`
- **pgvector not working?** Verify extension: `docker exec -it pgvector_db psql -U kb_user -d kb -c "\dx"`

## Files

- `.env` - Environment variables for Postgres
- `docker_compose.yaml` - Docker services configuration
- `init/01_pgvector.sql` - pgvector extension initialization
