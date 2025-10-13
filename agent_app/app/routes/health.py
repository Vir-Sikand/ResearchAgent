import os, json, requests, pymysql
from fastapi import APIRouter, HTTPException
from ..services.openai_client import client

router = APIRouter()

NIM_BASE = os.environ["NIM_API_BASE"]
NIM_KEY  = os.environ["NIM_API_KEY"]
RERANK_MODEL = os.environ.get("NIM_RERANK_MODEL","nvidia/llama-3.2-nv-rerankqa-1b-v2")
KB_NAME = os.environ.get("KB_NAME","org_kb_openai")

def _mdb_conn():
    return pymysql.connect(
        host=os.environ.get("MINDSDB_HOST","mindsdb"),
        port=int(os.environ.get("MINDSDB_PORT","47335")),
        user=os.environ.get("MINDSDB_USER","mindsdb"),
        password=os.environ.get("MINDSDB_PASSWORD",""),
        cursorclass=pymysql.cursors.DictCursor
    )

@router.get("/llm")
def llm():
    r = client.models.list()
    return {"ok": True, "models": [m.id for m in r.data][:5]}

@router.get("/rerank")
def rerank():
    """Test NIM reranking endpoint - may not be available on all NIM configurations"""
    hdrs = {"Authorization": f"Bearer {NIM_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": RERANK_MODEL,
        "query": {"text": "ping"},
        "passages": [{"text":"pong"}, {"text":"pang"}],
        "truncate": "END"
    }
    try:
        r = requests.post(f"{NIM_BASE}/ranking", headers=hdrs, data=json.dumps(payload), timeout=30)
        if r.status_code == 404:
            # Reranking endpoint not available - this is okay, will fail gracefully in actual use
            return {"ok": False, "available": False, "note": "Reranking endpoint not found (404). Reranking will be skipped in queries."}
        if not r.ok:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return {"ok": True, "available": True, "ranking": r.json()}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "available": False, "error": str(e)}

@router.get("/kb")
def kb_ping():
    # Simple: ensure we can SELECT from the KB (proves KB exists + MindsDB is reachable)
    # MindsDB requires database.table format
    q = f"SELECT * FROM mindsdb.{KB_NAME} LIMIT 1;"
    with _mdb_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(q)
            _ = cur.fetchall()
    return {"ok": True, "kb": KB_NAME, "sample_count": len(_)}

@router.get("/kb/search-test")
def kb_search_test():
    """Debug endpoint to test KB search"""
    from ..services.kb_service import search_kb
    results = search_kb("multi-agent systems", top_k=3)
    return {
        "query": "multi-agent systems",
        "num_results": len(results),
        "results": results[:2]  # Return first 2 for debugging
    }
