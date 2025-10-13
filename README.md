# KB Agent: Intelligent Knowledge Base with Document Understanding

A multi-tenant platform for creating domain-specialized knowledge base agents using **NVIDIA NIM (Nemotron, VILA)** and **GPT-Researcher MCP**. The system intelligently routes queries between your organizational knowledge base and deep web research, with support for document upload and analysis.

**Built for the [Agents for Impact Hackathon](https://luma.com/813gzkjk?tk=0EwYEu) at Santa Clara University.**

---

## 🎯 What It Does

Research teams face redundant research and scattered knowledge. This system solves that by:

1. ✅ **Document Understanding** - Upload PDFs, images, DOCX → NVIDIA VILA extracts text
2. ✅ **Checks KB First** - Semantic search finds existing knowledge
3. ✅ **Intelligent Routing** - Nemotron LLM decides KB vs research
4. ✅ **Auto-Research** - Triggers GPT-Researcher when KB lacks answers
5. ✅ **Builds Knowledge** - Research results automatically saved to KB
6. ✅ **User Control** - Override with `force:kb` or `force:research`

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              User Query + Documents (PDF/PNG/DOCX)          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
         ┌───────────────────────────┐
         │  VILA VLM Document Parser │
         │  Extract text from files  │
         └────────┬──────────────────┘
                  │
         ┌────────▼─────────────────┐
         │  Agent App (FastAPI)     │
         │  Port 8080               │
         └────────┬─────────────────┘
                  │
          ┌───────┴────────┐
          │  1. Search KB   │
          │  2. Rerank (NIM)│
          │  3. Assess      │
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
| **VLM Parser**      | NVIDIA VILA                          | PDF/Image/DOCX text extraction |
| **Routing LLM**     | NVIDIA Nemotron (NIM)                | Decision-making & answers      |
| **Embeddings**      | OpenAI text-embedding-3-small        | Semantic search                |
| **Reranker**        | NVIDIA NIM Reranker (optional)       | Improve search precision       |
| **Vector DB**       | PGVector                             | Embedding storage              |
| **KB Interface**    | MindsDB                              | SQL interface to KB            |
| **Deep Research**   | GPT-Researcher MCP                   | Web research with citations    |
| **Agent Framework** | FastAPI + Python                     | API & orchestration            |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- API Keys:
  - **NVIDIA NIM** - For Nemotron LLM & VILA VLM ([get key](https://build.nvidia.com/))
  - **OpenAI** - For embeddings ([get key](https://platform.openai.com/))
  - **Tavily** - For web search ([get key](https://tavily.com/))

### 1. Configure Environment

```bash
cp .env.template .env
# Edit .env with your API keys:
# - OPENAI_API_KEY=sk-...
# - TAVILY_API_KEY=tvly-...
# - NIM_API_KEY=nvapi-...  (used for both Nemotron and VILA)
```

### 2. Start All Services

```bash
docker compose up -d
docker compose ps  # Verify all 4 services running
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
```

### 4. Test It!

```bash
# Test document queries
python clients/test_document_query.py

# Test routing
python clients/test_routing.py

# Manual test
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How should we implement agent routing?"}'
```

---

## 📄 Document Upload & Analysis

### Supported Formats

| Format | Processing Method |
|--------|------------------|
| **PDF** | Each page → image → VILA VLM |
| **DOCX** | Convert to PDF → process like PDF |
| **PNG/JPG** | Direct VILA VLM processing |

### How It Works

1. **KB Search**: Uses your query ONLY (no documents) 
2. **Research**: Uses your query ONLY (no documents)
3. **Answer Generation**: LLM receives query + KB/research results + **parsed document context**

This prevents embedding size errors while providing rich document context for answers.

### Example: Upload PDF + Query

```python
import requests

with open('research_paper.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/api/query/with-documents',
        files={'files': ('paper.pdf', f, 'application/pdf')},
        data={
            'query': 'What are the key findings?',
            'override': 'force:kb'
        }
    )
    
print(response.json()['answer'])
```

### Example: Multiple Documents

```python
files = [
    ('files', ('paper.pdf', open('paper.pdf', 'rb'), 'application/pdf')),
    ('files', ('diagram.png', open('diagram.png', 'rb'), 'image/png'))
]

response = requests.post(
    'http://localhost:8080/api/query/with-documents',
    files=files,
    data={
        'query': 'Compare the information in these documents',
        'depth': 'deep'
    }
)
```

### Example: Bash/cURL

```bash
curl -X POST http://localhost:8080/api/query/with-documents \
  -F "files=@research_paper.pdf" \
  -F "files=@diagram.png" \
  -F "query=Summarize the key findings" \
  -F "depth=quick"
```

---

## 📡 API Reference

### 1. Standard Query: `/api/query`

**Request:**
```json
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
  "sources": [...],
  "route_taken": "kb_only | research_then_kb | research_only",
  "confidence": 0.87,
  "research_conducted": false
}
```

### 2. Document Query: `/api/query/with-documents`

**Request (multipart/form-data):**
```python
files = {'files': ('doc.pdf', file_object, 'application/pdf')}
data = {
    'query': 'Your question',         # Required
    'override': 'force:kb',           # Optional
    'depth': 'quick',                 # Optional
    'max_results': 12                 # Optional
}
```

**Response:** Same format as `/api/query`

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
```bash
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Internal docs", "override": "force:kb"}'
```

#### 3. Force Deep Research
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
GET /api/query/health  # Full routing system
```

---

## ⚙️ Configuration

Edit `.env` to customize behavior:

```bash
# === API Keys ===
OPENAI_API_KEY=sk-...              # For embeddings + gpt-researcher
TAVILY_API_KEY=tvly-...            # For web search
NIM_API_KEY=nvapi-...              # For Nemotron LLM & VILA VLM

# === NVIDIA NIM Models ===
NIM_API_BASE=https://integrate.api.nvidia.com/v1
NIM_LLM_MODEL=nvidia/llama-3.1-nemotron-ultra-253b-v1
NIM_RERANK_MODEL=nvidia/llama-3.2-nv-rerankqa-1b-v2

# === Routing Behavior ===
CONFIDENCE_THRESHOLD=0.7           # Min confidence to use KB only (0.0-1.0)
MIN_KB_RESULTS=3                   # Min KB results needed

# === Knowledge Base ===
KB_NAME=org_kb_openai              # MindsDB KB name
MINDSDB_HOST=127.0.0.1
MINDSDB_PORT=47335
```

**Tuning the Routing:**
- **Lower threshold (0.5-0.6)** → More KB-only (faster)  
- **Higher threshold (0.8-0.9)** → More research (comprehensive)

---

## 🧪 Testing

### Document Upload Tests

```bash
python clients/test_document_query.py
```

Tests:
- ✅ PDF parsing with KB search
- ✅ Image parsing with deep research
- ✅ Multiple files with smart routing
- ✅ Document + KB integration

### Routing Tests

```bash
python clients/test_routing.py
```

Tests:
- Force KB only
- Force research only
- Smart routing scenarios

---

## 🐛 Troubleshooting

### Document Upload Issues

**Problem:** Timeouts or connection errors when uploading documents

**Cause:** Large documents can take time to process (VILA processes each PDF page as an image)

**Solution:** 
- Be patient with large PDFs (processing is page-by-page)
- Check logs: `docker logs agent_app`
- Look for `[PDF→VLM]` and `[VILA]` messages to track progress

### Embedding Size Errors

**Problem:** `maximum context length is 8192 tokens, however you requested 21910 tokens`

**Solution:** Already fixed! The system now:
- Uses ONLY your query for KB search (fits in 8K limit)
- Uses documents as context for answer generation (no embedding needed)

### Services Won't Start

```bash
# Check all services
docker compose ps

# View logs
docker logs agent_app
docker logs mindsdb

# Restart a service
docker compose restart agent_app
```

### Health Checks Failing

```bash
# Test each health endpoint
curl http://localhost:8080/health/llm
curl http://localhost:8080/health/kb
curl http://localhost:8080/api/query/health
```

### KB Queries Fail

```bash
# Verify KB exists
mysql -h 127.0.0.1 --port 47335 -u mindsdb \
  -e "SELECT * FROM mindsdb.org_kb_openai LIMIT 1;"

# If KB doesn't exist, create it:
mysql -h 127.0.0.1 --port 47335 -u mindsdb < scripts/kb_create_openai.sql
```

### Reranker Not Working

The reranker endpoint may not be available - this is **okay**. The system falls back to original search order with slightly lower precision.

---

## 💡 Use Cases

### Research Team Workflow

**Scenario:** Researcher uploads a PDF and asks "What are the latest RAG techniques?"

1. **First time** → VILA extracts text → No KB results → Conducts research (18s)
2. **Research saved** → Added to KB automatically
3. **Second time** → Same question → Instant from KB (2s)
4. **Related questions** → KB has context from previous research

### Product Teams

Upload PRDs, specifications, diagrams → Ask:
- "What features are planned for Q4?"
- "Compare this design to our previous approach"
- "What experiments support this decision?" (triggers research)

### Academic Research

Upload papers, lab notes, charts:
- VILA extracts text from PDFs and diagrams
- Ask questions spanning multiple documents
- System combines internal knowledge with external research

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
│   │   │   ├── document_parser.py      # Multi-format doc parsing ⭐
│   │   │   ├── nim_vlm_parse.py        # VILA VLM integration ⭐
│   │   │   ├── kb_service.py           # KB search & rerank
│   │   │   ├── gpt_researcher_client.py # Research MCP client
│   │   │   └── openai_client.py        # OpenAI SDK
│   │   └── utils/
│   │       └── pdf_render.py           # PDF to image conversion
│   ├── Dockerfile
│   └── pyproject.toml
├── clients/               # Test & utility scripts
│   ├── test_document_query.py   # Document upload tests ⭐
│   ├── test_routing.py          # Routing tests
│   └── requirements.txt
├── scripts/
│   └── kb_create_openai.sql     # KB setup SQL
├── init/
│   └── 01_pgvector.sql          # PGVector initialization
├── mcp_server.py          # GPT-Researcher MCP server
├── docker-compose.yml     # All services
└── README.md             # This file
```

---

## 🏆 Hackathon Highlights

### ✅ NVIDIA Nemotron (Prize Category!)
- Core LLM for routing decisions
- Quality assessment of KB results
- Answer generation with citations
- Research synthesis
- Using `nvidia/llama-3.1-nemotron-ultra-253b-v1`

### ✅ NVIDIA VILA VLM
- PDF text extraction (page-by-page processing)
- Image OCR and understanding
- DOCX parsing (via PDF conversion)
- Using NVCF asset upload workflow

### ✅ NVIDIA NIM Integration
- Nemotron for intelligence
- VILA for document understanding
- Reranker for search quality (with graceful fallback)

### ✅ MCP Protocol
- GPT-Researcher as proper MCP server
- Extensible for more MCP servers
- Clean HTTP interface

### ✅ Full Working Application
- End-to-end functional system
- Document upload & analysis
- Production-ready architecture
- Comprehensive API

---

## 🔮 Future Enhancements

### Immediate
1. **Streaming Responses** - Real-time progress for long documents
2. **Batch Processing** - Upload entire document libraries
3. **More MCP Servers** - ArXiv, PubMed, Confluence integration

### Advanced
1. **Multi-Tenancy** - Separate KBs per team/org
2. **Feedback Loop** - Track answer quality, auto-tune
3. **Advanced Routing** - Time-sensitive query detection
4. **Hybrid Search** - Combine semantic + keyword search

---

## 📝 License

MIT License

---

## 🙏 Acknowledgments

- **NVIDIA** - NIM platform, Nemotron models, VILA VLM
- **GPT-Researcher** - Autonomous research framework
- **MindsDB** - Knowledge base & ML engine
- **Agents for Impact Hackathon** - Platform & inspiration

---

## 📧 Questions?

Built for the Agents for Impact Hackathon at Santa Clara University.

```bash
# Run the tests!
python clients/test_document_query.py
python clients/test_routing.py
```

**Happy hacking! 🚀**
