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
DROP KNOWLEDGE_BASE IF EXISTS org_kb_openai;
CREATE KNOWLEDGE_BASE org_kb_openai
USING
  storage = org_pg.storage_table,
  embedding_model = {
    "provider": "openai",
    "model_name": "text-embedding-3-small",
    "api_key": ${OPENAI_API_KEY}
  },
  content_columns  = ['text'],
  metadata_columns = ['title','page','source_uri'];
INSERT INTO org_kb_openai (text, title, page, source_uri)
VALUES ('Hello vectors from OpenAI!', 'Sanity', 1, 'local');
SELECT * FROM org_kb_openai WHERE content = 'hello vectors';