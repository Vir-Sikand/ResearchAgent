from fastapi import FastAPI
from .routes.health import router as health_router

app = FastAPI(title="KB Agents – Step 2 (KB uses NIM embeddings)")
app.include_router(health_router, prefix="/health")

@app.get("/")
def root():
    return {"ok": True, "msg": "Step 2: NIM wired; KB embeds via MindsDB+NIM"}