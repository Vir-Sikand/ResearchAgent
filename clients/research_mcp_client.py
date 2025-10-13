import os, json, argparse, requests
from dotenv import load_dotenv

# Usage:
#   python clients/research_mcp_client.py --url http://127.0.0.1:8000 --query "What is ..." --depth quick --k 12

def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
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
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    main()