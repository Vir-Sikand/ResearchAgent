from fastapi import FastAPI
from .routes.health import router as health_router
from .routes.query import router as query_router

app = FastAPI(
    title="KB Agent with Intelligent Routing",
    description="Domain-specialized knowledge base agent using NVIDIA NIM + GPT-Researcher MCP"
)

app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(query_router, prefix="/api", tags=["Query"])

@app.get("/")
def root():
    return {
        "ok": True,
        "msg": "KB Agent with intelligent routing (KB + GPT-Researcher)",
        "endpoints": {
            "query": "/api/query",
            "health": "/health/llm, /health/emb, /health/rerank, /health/kb",
            "query_health": "/api/query/health"
        }
    }