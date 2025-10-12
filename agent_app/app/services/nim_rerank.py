import os, json, requests
NIM_BASE = os.environ["NIM_API_BASE"]
NIM_KEY  = os.environ["NIM_API_KEY"]
RERANK_MODEL = os.environ.get("NIM_RERANK_MODEL","nvidia/llama-3.2-nv-rerankqa-1b-v2")

def rerank(query: str, passages: list[str]):
    hdrs = {"Authorization": f"Bearer {NIM_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": RERANK_MODEL,
        "query": {"text": query},
        "passages": [{"text": p} for p in passages],
        "truncate": "END"
    }
    r = requests.post(f"{NIM_BASE}/ranking", headers=hdrs, data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    return r.json()
