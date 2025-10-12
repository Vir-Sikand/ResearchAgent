"""
Query routing endpoint - the core of the agent system.

Routes queries to either KB-only or KB + deep research based on:
1. User override keywords (force:kb or force:research)
2. KB result quality (confidence and coverage)
3. Nemotron LLM assessment of whether KB results are sufficient
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal

from ..services.openai_client import client
from ..services.kb_service import search_and_rerank, insert_chunk
from ..services.gpt_researcher_client import conduct_research

router = APIRouter()

# Configuration
CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.7"))
MIN_KB_RESULTS = int(os.environ.get("MIN_KB_RESULTS", "3"))
NIM_LLM_MODEL = os.environ.get("NIM_LLM_MODEL", "nvidia/llama-3.1-nemotron-ultra-253b-v1")


class QueryRequest(BaseModel):
    query: str
    override: Optional[Literal["force:kb", "force:research"]] = None
    depth: str = "quick"  # for research: "quick" or "deep"
    max_results: int = 12  # for research


class Source(BaseModel):
    text: str
    title: Optional[str] = None
    page: Optional[int] = None
    source_uri: Optional[str] = None
    relevance_score: Optional[float] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    route_taken: str  # "kb_only", "research_then_kb", or "research_only"
    confidence: Optional[float] = None
    research_conducted: bool = False


def assess_kb_sufficiency(query: str, kb_results: List[dict], scores: List[float]) -> tuple[bool, str, float]:
    """
    Use Nemotron LLM to assess if KB results are sufficient to answer the query.
    
    Returns:
        (is_sufficient, reasoning, confidence_score)
    """
    if not kb_results:
        return False, "No KB results found", 0.0
    
    # Format KB results for LLM
    context = "\n\n".join([
        f"[Result {i+1}] (score: {scores[i]:.3f})\n"
        f"Title: {r.get('title', 'N/A')}\n"
        f"Source: {r.get('source_uri', 'N/A')}\n"
        f"Content: {r.get('text', '')[:500]}..."
        for i, r in enumerate(kb_results)
    ])
    
    prompt = f"""You are an AI assistant helping to assess whether existing knowledge base (KB) results can answer a user query.

User Query: {query}

KB Search Results:
{context}

Task: Analyze if the KB results contain sufficient information to answer the user's query comprehensively.

Consider:
1. Do the results directly address the query?
2. Is the information complete enough for a good answer?
3. Are the results recent/relevant enough?
4. Would external research provide significant additional value?

Respond in JSON format:
{{
  "sufficient": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

    try:
        response = client.chat.completions.create(
            model=NIM_LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )
        
        # Parse response
        import json
        result = json.loads(response.choices[0].message.content)
        
        return (
            result.get("sufficient", False),
            result.get("reasoning", ""),
            result.get("confidence", 0.5)
        )
        
    except Exception as e:
        # Fallback: use simple heuristics
        avg_score = sum(scores) / len(scores) if scores else 0
        sufficient = avg_score > CONFIDENCE_THRESHOLD and len(kb_results) >= MIN_KB_RESULTS
        return sufficient, f"Heuristic assessment (avg_score={avg_score:.3f})", avg_score


def generate_answer_from_kb(query: str, kb_results: List[dict]) -> str:
    """Generate a final answer using Nemotron based on KB results."""
    
    context = "\n\n".join([
        f"[Source {i+1}]\n"
        f"Title: {r.get('title', 'N/A')}\n"
        f"Content: {r.get('text', '')}"
        for i, r in enumerate(kb_results)
    ])
    
    prompt = f"""You are a helpful AI assistant. Answer the user's query using ONLY the information from the provided knowledge base sources.

User Query: {query}

Knowledge Base Sources:
{context}

Instructions:
- Provide a comprehensive, accurate answer
- Cite sources using [Source N] notation
- If information is incomplete, acknowledge it
- Do not add information not present in the sources

Answer:"""

    response = client.chat.completions.create(
        model=NIM_LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000
    )
    
    return response.choices[0].message.content


def generate_answer_from_research(query: str, research_report: str) -> str:
    """Generate a synthesized answer using Nemotron based on research results."""
    
    # If research report is too long, truncate it for the synthesis prompt
    # (keep full report in KB, just limit what we send to LLM)
    max_report_length = 8000  # characters
    report_for_synthesis = research_report[:max_report_length]
    if len(research_report) > max_report_length:
        report_for_synthesis += "\n\n[Note: Report truncated for synthesis. Full report available in sources.]"
    
    prompt = f"""You are a helpful AI assistant. The user asked a question, and deep research was conducted to answer it.

User Query: {query}

Research Report:
{report_for_synthesis}

Instructions:
- Synthesize the research into a clear, comprehensive answer to the user's specific query
- Focus on directly answering what the user asked
- Maintain factual accuracy from the research
- Structure the answer in a logical, easy-to-read format
- If the research is incomplete or doesn't fully answer the query, acknowledge it
- Keep the answer concise but thorough (aim for 300-500 words unless more detail is needed)

Answer:"""

    try:
        response = client.chat.completions.create(
            model=NIM_LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        answer = response.choices[0].message.content
        
        # Fallback if LLM returns empty response
        if not answer or answer.strip() == "":
            print("[WARNING] LLM returned empty synthesis, using research report directly")
            return research_report
        
        return answer
        
    except Exception as e:
        # If synthesis fails, fallback to returning the research report directly
        print(f"[ERROR] Failed to synthesize research: {e}")
        print("[FALLBACK] Returning research report directly")
        return research_report


@router.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """
    Main query endpoint with intelligent routing.
    
    Flow:
    1. Check for override keywords
    2. Search KB and rerank
    3. Use Nemotron to assess KB sufficiency
    4. Route to research if needed
    5. Generate final answer
    """
    query = request.query
    override = request.override
    
    # Handle force:kb override
    if override == "force:kb":
        kb_results, scores = search_and_rerank(query, top_k=8, rerank_top_n=5)
        
        if not kb_results:
            raise HTTPException(status_code=404, detail="No KB results found")
        
        answer = generate_answer_from_kb(query, kb_results)
        
        sources = [
            Source(
                text=r.get("text", ""),
                title=r.get("title"),
                page=r.get("page"),
                source_uri=r.get("source_uri"),
                relevance_score=scores[i] if i < len(scores) else None
            )
            for i, r in enumerate(kb_results)
        ]
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            route_taken="kb_only",
            confidence=sum(scores) / len(scores) if scores else 0.0,
            research_conducted=False
        )
    
    # Handle force:research override
    if override == "force:research":
        research_result = conduct_research(query, depth=request.depth, max_results=request.max_results)
        
        # Upsert full research report to KB for future reference
        insert_chunk(
            text=research_result.report,
            title=f"Research: {query[:80]}",
            page=1,
            source_uri="mcp:gpt-researcher"
        )
        
        # Generate synthesized answer from research using LLM
        synthesized_answer = generate_answer_from_research(query, research_result.report)
        
        sources = [Source(text=research_result.report, source_uri="mcp:gpt-researcher")]
        
        return QueryResponse(
            answer=synthesized_answer,
            sources=sources,
            route_taken="research_only",
            research_conducted=True
        )
    
    # Default: Smart routing
    # Step 1: Search KB
    kb_results, scores = search_and_rerank(query, top_k=8, rerank_top_n=5)
    
    # Step 2: Assess sufficiency using Nemotron
    is_sufficient, reasoning, confidence = assess_kb_sufficiency(query, kb_results, scores)
    
    # Step 3: Route decision
    if is_sufficient and kb_results:
        # KB is sufficient
        answer = generate_answer_from_kb(query, kb_results)
        
        sources = [
            Source(
                text=r.get("text", ""),
                title=r.get("title"),
                page=r.get("page"),
                source_uri=r.get("source_uri"),
                relevance_score=scores[i] if i < len(scores) else None
            )
            for i, r in enumerate(kb_results)
        ]
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            route_taken="kb_only",
            confidence=confidence,
            research_conducted=False
        )
    
    else:
        # KB insufficient - conduct research
        research_result = conduct_research(query, depth=request.depth, max_results=request.max_results)
        
        # Upsert full research report to KB for future reference
        insert_chunk(
            text=research_result.report,
            title=f"Research: {query[:80]}",
            page=1,
            source_uri="mcp:gpt-researcher"
        )
        
        # Generate synthesized answer from research using LLM
        synthesized_answer = generate_answer_from_research(query, research_result.report)
        
        # Combine KB results with research
        all_sources = [
            Source(
                text=r.get("text", ""),
                title=r.get("title"),
                page=r.get("page"),
                source_uri=r.get("source_uri"),
                relevance_score=scores[i] if i < len(scores) else None
            )
            for i, r in enumerate(kb_results)
        ]
        
        all_sources.append(Source(
            text=research_result.report,
            title=f"Research: {query[:80]}",
            source_uri="mcp:gpt-researcher"
        ))
        
        return QueryResponse(
            answer=synthesized_answer,
            sources=all_sources,
            route_taken="research_then_kb",
            confidence=confidence,
            research_conducted=True
        )


@router.get("/query/health")
def query_health():
    """Health check for query routing system"""
    from ..services.gpt_researcher_client import health_check
    
    gptr_healthy = health_check()
    
    return {
        "ok": True,
        "gpt_researcher_connected": gptr_healthy,
        "nim_llm_model": NIM_LLM_MODEL,
        "confidence_threshold": CONFIDENCE_THRESHOLD
    }

