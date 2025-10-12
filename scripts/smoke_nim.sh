#!/usr/bin/env bash
set -euo pipefail
: "${NIM_API_BASE?}"; : "${NIM_API_KEY?}"

echo "1) /models"
curl -fsS "$NIM_API_BASE/models" -H "Authorization: Bearer $NIM_API_KEY" >/dev/null

echo "2) chat"
curl -fsS "$NIM_API_BASE/chat/completions" \
 -H "Authorization: Bearer $NIM_API_KEY" -H "Content-Type: application/json" \
 -d '{"model":"'"${NIM_LLM_MODEL:-nvidia/llama-3.3-70b-instruct}"'","messages":[{"role":"user","content":"Say hi in 5 words."}]}' >/dev/null

echo "3) embeddings (query)"
curl -fsS "$NIM_API_BASE/embeddings" \
 -H "Authorization: Bearer $NIM_API_KEY" -H "Content-Type: application/json" \
 -d '{"model":"nvidia/nv-embedqa-e5-v5-query","input":["ping"],"modality":"text"}' >/dev/null

echo "4) reranking"
curl -fsS "$NIM_API_BASE/ranking" \
 -H "Authorization: Bearer $NIM_API_KEY" -H "Content-Type: application/json" \
 -d '{"model":"'"${NIM_RERANK_MODEL:-nvidia/llama-3.2-nv-rerankqa-1b-v2}"'","query":{"text":"firmware update step"},"passages":[{"text":"Power cycle."},{"text":"Use Settings > Firmware > Update."}]}' >/dev/null

echo "OK ✓"
