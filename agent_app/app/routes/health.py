import os, json, requests, pymysql
from fastapi import APIRouter, HTTPException
from ..services.openai_client import client

router = APIRouter()

NIM_BASE = os.environ["NIM_API_BASE"]
NIM_KEY  = os.environ["NIM_API_KEY"]
RERANK_MODEL = os.environ.get("NIM_RERANK_MODEL","nvidia/llama-3.2-nv-rerankqa-1b-v2")
KB_NAME = os.environ.get("KB_NAME","org_kb_nim")

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

@router.get("/emb")
def emb():
    # Embeddings smoke via chat models list is sufficient; MindsDB will call NIM during KB insert/query.
    # We still do a lightweight embeddings call to verify dims.
    r = client.embeddings.create(model="nvidia/nv-embedqa-e5-v5-query", input=["ping"], modality="text")
    return {"ok": True, "dims": len(r.data[0].embedding)}

@router.get("/rerank")
def rerank():
    hdrs = {"Authorization": f"Bearer {NIM_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": RERANK_MODEL,
        "query": {"text": "ping"},
        "passages": [{"text":"pong"}, {"text":"pang"}],
        "truncate": "END"
    }
    r = requests.post(f"{NIM_BASE}/ranking", headers=hdrs, data=json.dumps(payload), timeout=30)
    if not r.ok:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return {"ok": True, "ranking": r.json()}

@router.get("/kb")
def kb_ping():
    # Simple: ensure we can SELECT from the KB (proves KB exists + MindsDB is reachable)
    q = f"SELECT * FROM {KB_NAME} LIMIT 1;"
    with _mdb_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(q)
            _ = cur.fetchall()
    return {"ok": True, "kb": KB_NAME, "sample_count": len(_)}
