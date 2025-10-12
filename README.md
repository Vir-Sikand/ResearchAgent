# KB Agent: Intelligent Knowledge Base System with Research Routing

A multi-tenant platform for creating domain-specialized knowledge base agents using **NVIDIA NIM (Nemotron)** and **GPT-Researcher MCP**. The system intelligently routes queries between your organizational knowledge base and deep web research, automatically building institutional memory over time.

**Built for the [Agents for Impact Hackathon](https://luma.com/813gzkjk?tk=0EwYEu) at Santa Clara University.**

---

## 🎯 What It Does

Research teams face a common problem: **redundant research**. Researchers spend time investigating questions that colleagues have already answered, or waste effort on comprehensive research when internal docs could suffice.

This system solves that by:
1. ✅ **Checking your KB first** - Uses semantic search to find existing knowledge
2. ✅ **Intelligent routing** - NVIDIA Nemotron LLM decides if KB is sufficient or research is needed
3. ✅ **Auto-research** - Triggers GPT-Researcher MCP when KB lacks answers
4. ✅ **Builds knowledge** - Research results automatically saved to KB
5. ✅ **User control** - Override with keywords: `force:kb` or `force:research`

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
         ┌───────────────────────────┐
         │  Agent App (FastAPI)      │
         │  Port 8080                │
         └────────┬──────────────────┘
                  │
          ┌───────┴────────┐
          │  1. Parse Query │
          │  2. Search KB   │
          │  3. Rerank (NIM)│
          │  4. Assess      │
          └───────┬─────────┘
                  │
         ┌────────┴─────────┐
         │                  │
    Sufficient?        Insufficient?
         │                  │
         ▼                  ▼
┌─────────────────┐   ┌──────────────────┐
│ MindsDB KB      │   │ GPT-Researcher   │
│ + PGVector      │   │ MCP (Port 8000)  │
│ OpenAI Embed    │   │ Web Research     │
└────────┬────────┘   └────────┬─────────┘
         │                     │
         │                     │ (upsert)
         │                     ▼
         │            ┌──────────────────┐
         └───────────►│ Nemotron (NIM)   │
                      │ Generate Answer  │
                      └──────────────────┘
```

### Tech Stack

| Component           | Technology                           | Purpose                        |
|---------------------|--------------------------------------|--------------------------------|
| **Routing LLM**     | NVIDIA Nemotron (NIM)                | Decision-making & answers      |
| **Embeddings**      | OpenAI text-embedding-3-small        | Semantic search                |
| **Reranker**        | NVIDIA NIM Reranker (optional)       | Improve search precision       |
| **VLM Parser**      | NVIDIA NeMo Retriever (ready)        | Parse PDFs/documents           |
| **Vector DB**       | PGVector                             | Embedding storage              |
| **KB Interface**    | MindsDB                              | SQL interface to KB            |
| **Deep Research**   | GPT-Researcher MCP                   | Web research with citations    |
| **Agent Framework** | FastAPI + Python                     | API & orchestration            |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- API Keys:
  - **NVIDIA NIM** - For Nemotron LLM ([get key](https://build.nvidia.com/))
  - **OpenAI** - For embeddings ([get key](https://platform.openai.com/))
  - **Tavily** - For web search ([get key](https://tavily.com/))

### 1. Configure Environment

```bash
cp .env.template .env
# Edit .env with your API keys:
# - OPENAI_API_KEY=sk-...
# - TAVILY_API_KEY=tvly-...
# - NIM_API_KEY=nvapi-...
```

### 2. Start All Services

```bash
docker compose up -d
docker compose ps  # Verify all 4 services running
```

**Development Mode:** Code changes auto-reload! The `agent_app` service has volume mounts enabled, so you can edit Python files and see changes immediately without rebuilding.

**Note:** Environment variable changes (`.env` file) require restarting the container:
```bash
docker compose up -d agent-app  # Pick up new env vars
```

**Services:**
- `postgres` (5432) - PGVector storage
- `mindsdb` (47334, 47335) - KB + SQL interface
- `gpt_researcher_mcp` (8000) - Research service
- `agent_app` (8080) - Main API

### 3. Create Knowledge Base

```bash
# Run setup SQL (only once)
mysql -h 127.0.0.1 --port 47335 -u mindsdb < scripts/kb_create_openai.sql

# Or via MindsDB GUI at http://localhost:47334
```

### 4. Test It!

```bash
# Run automated test suite
python clients/test_routing.py

# Or manual test:
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How should we implement agent routing?"}'
```

---

## 📡 API Reference

### Main Endpoint: `/api/query`

**Request:**
```bash
POST http://localhost:8080/api/query
Content-Type: application/json

{
  "query": "Your question here",
  "override": null,          // or "force:kb" | "force:research"
  "depth": "quick",          // or "deep" (for research)
  "max_results": 12          // num sources for research
}
```

**Response:**
```json
{
  "answer": "Comprehensive answer with citations...",
  "sources": [
    {
      "text": "Source content...",
      "title": "Document Title",
      "page": 5,
      "source_uri": "internal://prd/2024-q4",
      "relevance_score": 0.89
    }
  ],
  "route_taken": "kb_only | research_then_kb | research_only",
  "confidence": 0.87,
  "research_conducted": false
}
```

### Routing Modes

#### 1. Smart Routing (Default)
Nemotron assesses KB quality and decides automatically:

```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is our product roadmap?"}'
```

**Flow:**
1. Search KB → 8 results
2. Rerank → Top 5 by relevance
3. Nemotron assesses → `{sufficient: true, confidence: 0.85}`
4. Route: **KB only** → Generate answer

#### 2. Force KB Only
Only search internal knowledge base:

```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Internal docs", "override": "force:kb"}'
```

#### 3. Force Deep Research
Always conduct web research (skip KB):

```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Latest AI trends 2025",
    "override": "force:research",
    "depth": "deep"
  }'
```

### Health Checks

```bash
GET /health/llm        # NVIDIA Nemotron LLM
GET /health/rerank     # NVIDIA Reranker (optional)
GET /health/kb         # MindsDB + PGVector KB
GET /api/query/health  # Full routing system + gpt-researcher
```

---

## ⚙️ Configuration

Edit `.env` to customize behavior:

```bash
# === API Keys ===
OPENAI_API_KEY=sk-...              # For embeddings + gpt-researcher
TAVILY_API_KEY=tvly-...            # For web search
NIM_API_KEY=nvapi-...              # For Nemotron LLM

# === NVIDIA NIM Models ===
NIM_API_BASE=https://integrate.api.nvidia.com/v1
NIM_LLM_MODEL=nvidia/llama-3.1-nemotron-ultra-253b-v1
NIM_RERANK_MODEL=nvidia/llama-3.2-nv-rerankqa-1b-v2
NIM_VLM_PARSER_MODEL=nvidia/nemoretriever-parse

# === Routing Behavior ===
CONFIDENCE_THRESHOLD=0.7           # Min confidence to use KB only (0.0-1.0)
MIN_KB_RESULTS=3                   # Min KB results needed

# === Knowledge Base ===
KB_NAME=org_kb_openai              # MindsDB KB name
MINDSDB_HOST=127.0.0.1             # For host machine scripts
MINDSDB_PORT=47335

# === Postgres (PGVector) ===
POSTGRES_DB=kb
POSTGRES_USER=kb_user
POSTGRES_PASSWORD=kb_pass_123
```

### Tuning the Routing

**Lower threshold (0.5-0.6)** → More KB-only (faster, uses existing knowledge)  
**Higher threshold (0.8-0.9)** → More research (comprehensive, always fresh)

---

## 🔧 How It Works Internally

### 1. Query Processing

```python
# User query arrives
query = "How do multi-agent systems work?"

# Check for override keywords
if "force:kb" in override:
    return answer_from_kb(query)
elif "force:research" in override:
    return conduct_research(query)
```

### 2. KB Search & Rerank

```python
# Semantic search via MindsDB
results = search_kb(query, top_k=8)
# → Returns documents with OpenAI embeddings

# Rerank with NVIDIA NIM (if available)
reranked, scores = rerank(query, results)
# → Reorders by relevance using cross-encoder
```

### 3. Nemotron Assessment

```python
# Nemotron analyzes KB quality
assessment = nemotron.assess(query, kb_results, scores)
# → {
#     "sufficient": true/false,
#     "confidence": 0.85,
#     "reasoning": "KB contains detailed docs..."
#   }

if assessment.sufficient:
    return generate_answer_from_kb(query, kb_results)
```

### 4. Research Fallback

```python
# KB insufficient → trigger research
research = gpt_researcher.conduct(query, depth="quick")
# → Returns comprehensive report with citations

# Synthesize research into focused answer using Nemotron
synthesized_answer = generate_answer_from_research(query, research.report)
# → LLM creates concise, query-focused response (300-500 words)

# Auto-save FULL research report to KB for future queries
insert_to_kb(research.report, source="mcp:gpt-researcher")

# Return synthesized answer (full report available in sources)
return synthesized_answer
```

---

## 💡 Use Cases

### Research Team Workflow

**Scenario:** Researcher asks "What are the latest RAG techniques?"

1. **First time** → No KB results → Conducts web research (18s)
2. **Research saved** → Added to KB automatically
3. **Second time** → Same question → Instant answer from KB (2s)
4. **Related questions** → "How does RAG compare to fine-tuning?" → KB has context

**Benefits:**
- ✅ No redundant research
- ✅ Institutional memory grows
- ✅ Faster answers over time
- ✅ Full citation tracking

### Product Teams

Upload PRDs, specifications, lab notes → Ask questions like:
- "What features are planned for Q4?"
- "What experiments have we tried for feature X?"
- "Compare our approach to industry standards" (triggers research)

### Academic Research

Integrate with domain-specific sources:
- ArXiv MCP for papers
- PubMed MCP for biomedical research
- Internal lab notebooks

---

## 🗂️ Managing Your Knowledge Base

### Add Documents via MindsDB

```sql
-- Insert text documents
INSERT INTO mindsdb.org_kb_openai (text, title, page, source_uri)
VALUES 
  ('Our PRD specifies agent routing...', 'Product Roadmap Q4', 1, 'prd-2024-q4'),
  ('Lab experiment results...', 'Experiment Log', 1, 'lab-2024-10');

-- Search semantically
SELECT * FROM mindsdb.org_kb_openai 
WHERE content = 'agent routing architecture' 
LIMIT 5;
```

### Add Documents via Python

```python
from agent_app.app.services.kb_service import insert_chunk

# Insert a document chunk
insert_chunk(
    text="Your document content here...",
    title="Document Title",
    page=1,
    source_uri="docs/technical-spec.pdf"
)
```

### Add Documents via Research

```bash
# Research automatically saves results to KB
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Latest trends in vector databases",
    "override": "force:research"
  }'

# Now it's searchable from KB!
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "vector database trends"}'
```

---

## 📊 Service Details

### PostgreSQL + PGVector

```bash
# Container: pgvector_db
# Port: 5432
# Database: kb
# User: kb_user
# Password: kb_pass_123

# Verify pgvector extension
docker exec -it pgvector_db psql -U kb_user -d kb -c "\dx"
```

### MindsDB

```bash
# Container: mindsdb
# HTTP GUI: http://localhost:47334
# MySQL API: localhost:47335

# Connect via MySQL CLI
mysql -h 127.0.0.1 --port 47335 -u mindsdb

# Or use GUI for visual KB management
open http://localhost:47334
```

### GPT-Researcher MCP

```bash
# Container: gpt_researcher_mcp
# Port: 8000

# Health check
curl http://localhost:8000/health

# Direct research call (bypassing agent)
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?", "depth": "quick"}'
```

### Agent App

```bash
# Container: agent_app
# Port: 8080

# Root endpoint
curl http://localhost:8080

# View OpenAPI docs
open http://localhost:8080/docs
```

---

## 🧪 Testing

### Automated Test Suite

```bash
python clients/test_routing.py
```

**Tests:**
1. Force KB only
2. Force research only
3. Smart routing (KB expected)
4. Smart routing (research expected)

### Manual Testing

```bash
# Test force KB
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "override": "force:kb"}'

# Test force research
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "latest AI news", "override": "force:research"}'

# Test smart routing
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "your question here"}'
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check all services
docker compose ps

# View logs
docker logs agent_app
docker logs mindsdb
docker logs gpt_researcher_mcp
docker logs pgvector_db

# Restart a service
docker compose restart agent_app
```

### Health Checks Failing

```bash
# Test each health endpoint
curl http://localhost:8080/health/llm
curl http://localhost:8080/health/kb
curl http://localhost:8080/api/query/health

# Common issue: Wrong model name
# Fix: Verify NIM_LLM_MODEL in .env
# Should be: nvidia/llama-3.1-nemotron-70b-instruct
```

### KB Queries Fail

```bash
# Verify KB exists
mysql -h 127.0.0.1 --port 47335 -u mindsdb -e "SHOW DATABASES;"
mysql -h 127.0.0.1 --port 47335 -u mindsdb -e "SELECT * FROM mindsdb.org_kb_openai LIMIT 1;"

# If KB doesn't exist, create it:
mysql -h 127.0.0.1 --port 47335 -u mindsdb < scripts/kb_create_openai.sql
```

### Reranker Not Working

The reranker endpoint may not be available on all NIM configurations. This is **okay** - the system will gracefully fall back to original search order:

```bash
curl http://localhost:8080/health/rerank
# → {"ok": false, "available": false, "note": "Reranking endpoint not found"}
```

Queries still work without reranking, just with slightly lower precision.

### Research Takes Too Long

```bash
# Use quick mode (default)
{"query": "...", "depth": "quick"}  # ~10-20s

# Deep mode is comprehensive but slower
{"query": "...", "depth": "deep"}   # ~60-120s

# Increase max_results for more sources
{"query": "...", "max_results": 20}
```

### Common Error Codes

| Error | Cause | Solution |
|-------|-------|----------|
| 500 - Internal Server Error | Service connection issue | Check docker logs, verify .env |
| 404 - Model not found | Wrong NIM model name | Fix NIM_LLM_MODEL in .env (should be `nvidia/llama-3.1-nemotron-ultra-253b-v1`) |
| 1221 - Invalid database | Missing `mindsdb.` prefix | Update queries to use `mindsdb.KB_NAME` |
| Connection refused | Docker network issue | Use service names, not localhost |

---

## 🏆 Hackathon Highlights

This project demonstrates:

### ✅ NVIDIA Nemotron (Prize Category!)
- Core LLM for routing decisions
- Quality assessment of KB results
- Answer generation with citations
- Research synthesis into focused responses
- Using `nvidia/llama-3.1-nemotron-ultra-253b-v1`

### ✅ NVIDIA NIM Integration
- Nemotron for intelligence
- Reranker for search quality (with graceful fallback)
- VLM parser ready for document ingestion

### ✅ MCP Protocol
- GPT-Researcher as proper MCP server
- Extensible for more MCP servers (ArXiv, PubMed, Confluence)
- Clean HTTP interface

### ✅ Full Working Application
- End-to-end functional system
- Production-ready architecture
- Docker-based deployment
- Comprehensive API

### ✅ Real-World Value
- Solves actual research team problems
- Prevents redundant work
- Builds institutional memory
- Saves researcher time

---

## 🎬 Demo Script

For judges/presentation:

### 1. Show System Health (10 seconds)
```bash
curl http://localhost:8080/api/query/health | jq
```

### 2. Demo Force Research (20 seconds)
```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are latest trends in RAG 2025?", "override": "force:research"}' \
  | jq .route_taken
```

### 3. Query Same Topic Again (10 seconds)
```bash
# Now it's instant from KB!
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG trends"}' \
  | jq '{route: .route_taken, time: .response_time}'
```

### 4. Show Nemotron Decision Making (15 seconds)
```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Your KB content here"}' \
  | jq '{confidence: .confidence, route: .route_taken}'
```

**Key Points to Emphasize:**
1. **Nemotron makes intelligent decisions** (not just thresholds)
2. **Knowledge accumulates automatically** (research → KB)
3. **Prevents redundant work** (check KB first)
4. **Full provenance tracking** (all sources cited)

---

## 📁 Project Structure

```
dummy_hack/
├── agent_app/              # Main agent application
│   ├── app/
│   │   ├── main.py        # FastAPI app entry
│   │   ├── routes/
│   │   │   ├── query.py   # Main routing logic ⭐
│   │   │   └── health.py  # Health checks
│   │   ├── services/
│   │   │   ├── kb_service.py           # KB search & rerank
│   │   │   ├── gpt_researcher_client.py # Research MCP client
│   │   │   ├── openai_client.py        # OpenAI SDK
│   │   │   ├── nim_rerank.py           # NIM reranker
│   │   │   └── nim_vlm_parse.py        # VLM document parser
│   │   └── utils/
│   ├── Dockerfile
│   └── pyproject.toml
├── clients/               # Test & utility scripts
│   ├── test_routing.py   # Automated test suite
│   ├── research_mcp_client.py
│   └── run_research_and_upsert.py
├── scripts/
│   └── kb_create_openai.sql  # KB setup SQL
├── init/
│   └── 01_pgvector.sql       # PGVector initialization
├── mcp_server.py          # GPT-Researcher MCP server
├── docker-compose.yml     # All services
├── .env.template          # Configuration template
└── README.md             # This file
```

---

## 🔮 Future Enhancements

### Immediate (Post-Hackathon)

1. **Document Upload Endpoint**
   - Use VLM parser (`nim_vlm_parse.py`)
   - Parse PDFs, images, scanned docs
   - Auto-chunk and embed

2. **More MCP Servers**
   - ArXiv for academic papers
   - PubMed for biomedical research
   - Confluence/Jira for enterprise docs
   - SharePoint for corporate knowledge

3. **Streaming Responses**
   - Real-time KB search progress
   - Stream research as it happens
   - Better UX for long queries

### Advanced

1. **Multi-Tenancy**
   - Separate KBs per team/org
   - API key auth
   - Usage tracking & quotas

2. **Feedback Loop**
   - User ratings on answers
   - Track KB vs research performance
   - Auto-tune thresholds

3. **Advanced Routing**
   - Detect time-sensitive queries
   - Route by query complexity
   - Domain-specific routing rules

4. **Hybrid Search**
   - Combine semantic + keyword search
   - BM25 + vector similarity
   - Better recall

---

## 📝 License

MIT License - See project for details

---

## 🙏 Acknowledgments

- **NVIDIA** - NIM platform & Nemotron models
- **GPT-Researcher** - Autonomous research framework
- **MindsDB** - Knowledge base & ML engine
- **Agents for Impact Hackathon** - Inspiration & platform

---

## 📧 Questions?

Built for the Agents for Impact Hackathon at Santa Clara University.

For questions about this implementation, see the code or run the test suite!

```bash
python clients/test_routing.py
```

**Happy hacking! 🚀**
