import os, json, argparse, pymysql, requests
from dotenv import load_dotenv

def upsert_into_kb(conn, kb_table, report_text, citations, query):
    # Minimal upsert: one row for the full report. You can also split per section.
    title = f"GPTR: {query[:80]}"
    source_uri = "mcp:gpt-researcher"
    page = 1
    
    # Truncate content to avoid SQL parsing issues
    max_length = 10000  # Limit content length
    clean_content = report_text[:max_length] if len(report_text) > max_length else report_text
    
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {kb_table} (text, title, page, source_uri) VALUES (%s, %s, %s, %s)",
            (clean_content, title, page, source_uri)
        )
    conn.commit()

def run():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--kb", default=os.getenv("KB_NAME","org_kb_openai"))
    parser.add_argument("--query", required=True)
    parser.add_argument("--depth", default="quick", choices=["quick","deep"])
    parser.add_argument("--k", type=int, default=12)
    args = parser.parse_args()

    # Prepare headers
    headers = {
        "Content-Type": "application/json"
    }
    if os.getenv("OPENAI_API_KEY"):
        headers["x-openai-key"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("TAVILY_API_KEY"):
        headers["x-tavily-key"] = os.getenv("TAVILY_API_KEY")

    # Make request to research endpoint
    payload = {
        "query": args.query,
        "depth": args.depth,
        "max_results": args.k
    }

    try:
        response = requests.post(f"{args.url}/research", json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        report = result.get("report", "")
        citations = result.get("citations", [])
        
    except requests.exceptions.RequestException as e:
        print(f"Error making research request: {e}")
        return

    # connect to MindsDB SQL (MySQL wire)
    conn = pymysql.connect(
        host=os.getenv("MINDSDB_HOST","127.0.0.1"),
        port=int(os.getenv("MINDSDB_PORT","47335")),
        user=os.getenv("MINDSDB_USER","mindsdb"),
        password=os.getenv("MINDSDB_PASSWORD",""),
        database=os.getenv("MINDSDB_DB","mindsdb"),
        autocommit=False,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor
    )
    try:
        upsert_into_kb(conn, args.kb, report, citations, args.query)
        print(json.dumps({"status":"ok","kb":args.kb,"len_report":len(report),"citations":citations}, indent=2))
    finally:
        conn.close()

if __name__ == "__main__":
    run()
