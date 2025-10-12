CREATE DATABASE IF NOT EXISTS org_pg
WITH ENGINE = 'pgvector',
PARAMETERS = {
  "host": "postgres",
  "port": 5432,
  "database": "kb",
  "user": "kb_user",
  "password": "kb_pass_123",
  "distance": "cosine"
};
DROP KNOWLEDGE_BASE IF EXISTS org_kb_nim;
CREATE KNOWLEDGE_BASE org_kb_nim
USING
  storage = org_pg.storage_table,
  embedding_model = {
    "provider": "openai",
    "base_url": "https://integrate.api.nvidia.com/v1",
    "model_name": "nvidia/nv-embedqa-e5-v5",
    "api_key": "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"
  },
  content_columns  = ['text'],
  metadata_columns = ['title','page','source_uri'];
INSERT INTO org_kb_nim (text, title, page, source_uri)
VALUES ('Hello vectors from NIM!', 'Sanity', 1, 'local');
SELECT * FROM org_kb_nim WHERE content = 'hello vectors';