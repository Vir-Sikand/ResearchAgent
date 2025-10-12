# Minimal MindsDB SQL client used for INSERTing chunks (KB embeds via NIM server-side)
import os, pymysql
KB_NAME = os.environ.get("KB_NAME","org_kb_nim")

def _conn():
    return pymysql.connect(
        host=os.environ.get("MINDSDB_HOST","mindsdb"),
        port=int(os.environ.get("MINDSDB_PORT","47335")),
        user=os.environ.get("MINDSDB_USER","mindsdb"),
        password=os.environ.get("MINDSDB_PASSWORD",""),
        cursorclass=pymysql.cursors.DictCursor
    )

def insert_chunk(text: str, title: str|None, page: int|None, source_uri: str|None):
    # MindsDB requires database.table format
    sql = f"INSERT INTO mindsdb.{KB_NAME} (text, title, page, source_uri) VALUES (%s, %s, %s, %s);"
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (text, title, page, source_uri))
        conn.commit()
