"""Client for calling GPT-Researcher MCP service"""
import os
import requests
from typing import Dict, List, Optional

GPT_RESEARCHER_URL = os.environ.get("GPT_RESEARCHER_URL", "http://gpt_researcher_mcp:8000")


class ResearchResult:
    def __init__(self, report: str, query: str, citations: List[str]):
        self.report = report
        self.query = query
        self.citations = citations


def conduct_research(query: str, depth: str = "quick", max_results: int = 12) -> ResearchResult:
    """
    Call the GPT-Researcher MCP service to conduct deep research.
    
    Args:
        query: The research query
        depth: "quick" or "deep"
        max_results: Maximum number of sources to use
        
    Returns:
        ResearchResult with report, query, and citations
    """
    try:
        response = requests.post(
            f"{GPT_RESEARCHER_URL}/research",
            json={
                "query": query,
                "depth": depth,
                "max_results": max_results
            },
            timeout=300  # 5 minutes for deep research
        )
        response.raise_for_status()
        
        data = response.json()
        return ResearchResult(
            report=data.get("report", ""),
            query=data.get("query", query),
            citations=data.get("citations", [])
        )
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to conduct research: {str(e)}")


def health_check() -> bool:
    """Check if GPT-Researcher service is available"""
    try:
        response = requests.get(f"{GPT_RESEARCHER_URL}/health", timeout=5)
        return response.ok
    except:
        return False

