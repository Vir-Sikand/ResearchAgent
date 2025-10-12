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

CREATE ML_ENGINE nim_openai
FROM openai
USING
  api_key = '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',
  base_url = 'https://integrate.api.nvidia.com/v1';

DROP KNOWLEDGE_BASE IF EXISTS org_kb_openai;
CREATE KNOWLEDGE_BASE org_kb_openai
USING
  storage = org_pg.storage_table,
  embedding_model = {
    "provider": "openai",
    "model_name": "text-embedding-3-small",  
    "api_key": "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"
  },
  content_columns  = ['text'],
  metadata_columns = ['title','page','source_uri'];

INSERT INTO org_kb_openai (text, title, page, source_uri)
VALUES ('Hello vectors from NIM!', 'Sanity', 1, 'local');
SELECT * FROM org_kb_openai WHERE content = 'hello vectors';

