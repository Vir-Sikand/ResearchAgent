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
- `.env.example` - Template for API keys and configuration
- `docker-compose.yml` - Docker services configuration
- `docker-compose.gptr.yml` - GPT-Researcher MCP service
- `init/01_pgvector.sql` - pgvector extension initialization
- `clients/` - MCP client scripts for research and KB upsert
- `mcp/gptr-mcp/Dockerfile` - Alternative Dockerfile for GPT-Researcher

---

# GPT-Researcher MCP Setup

This section adds GPT-Researcher MCP server capabilities to your existing setup.

## Quick Start

### 1. Set up API keys

```bash
cp .env.example .env
# Edit .env and add your real API keys:
# - OPENAI_API_KEY=sk-your-key-here
# - TAVILY_API_KEY=tvly-your-key-here
```

### 2. Start GPT-Researcher MCP

```bash
docker compose -f docker-compose.gptr.yml --env-file .env up -d
docker logs -f gpt_researcher_mcp   # watch for "listening on :8000"
```

### 3. Install client dependencies

```bash
cd clients
pip install -r requirements.txt
```

### 4. Test the MCP connection

```bash
python research_mcp_client.py --url http://127.0.0.1:8000/sse \
  --query "Key trends in retrieval-augmented generation for enterprise KBs" \
  --depth quick --k 12
```

### 5. Research and upsert to KB

```bash
python run_research_and_upsert.py --url http://127.0.0.1:8000/sse \
  --kb org_kb_openai \
  --query "How should we route between KB and web research for hardware PRDs?" \
  --depth deep --k 16
```

### 6. Verify research is searchable

```sql
SELECT * FROM org_kb_openai WHERE content = 'KB vs web research routing for hardware PRDs';
```

## Services Overview

- **MindsDB + pgvector**: Ports 47334 (GUI), 47335 (MySQL API), 5432 (Postgres)
- **GPT-Researcher MCP**: Port 8000 (SSE endpoint)

## Troubleshooting

- **MCP server not starting?** Check `docker logs gpt_researcher_mcp` for entrypoint errors
- **Tool not found?** The client looks for tools named: `deep_research`, `research.run`, `research`, `run_research`
- **KB upsert failing?** Verify your KB exists and MindsDB connection settings in `.env`
