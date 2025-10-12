"""Knowledge Base search and retrieval service"""
import os
import json
import pymysql
from typing import List, Dict, Optional
from .nim_rerank import rerank

KB_NAME = os.environ.get("KB_NAME", "org_kb_openai")


def _conn():
    """Create MindsDB connection"""
    return pymysql.connect(
        host=os.environ.get("MINDSDB_HOST", "mindsdb"),
        port=int(os.environ.get("MINDSDB_PORT", "47335")),
        user=os.environ.get("MINDSDB_USER", "mindsdb"),
        password=os.environ.get("MINDSDB_PASSWORD", ""),
        cursorclass=pymysql.cursors.DictCursor
    )


def search_kb(query: str, top_k: int = 8) -> List[Dict]:
    """
    Search the knowledge base using semantic search.
    
    Args:
        query: The search query
        top_k: Number of results to return
        
    Returns:
        List of KB results with text, title, page, source_uri
    """
    # MindsDB semantic search: SELECT * with WHERE content = 'query'
    # Returns: id, chunk_content, metadata columns
    # Must use database.table format
    # Note: Using string formatting because MindsDB semantic search needs direct string
    sql = f"SELECT * FROM mindsdb.{KB_NAME} WHERE content = '{query}' LIMIT {top_k};"
    
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            raw_results = cur.fetchall()
    
    # Transform to expected format (text, title, page, source_uri)
    results = []
    for row in raw_results:
        # MindsDB returns: chunk_content (text), metadata (JSON with title, page, source_uri)
        text_content = row.get("chunk_content") or row.get("text") or row.get("content", "")
        
        # Parse metadata if it's a JSON string
        metadata = row.get("metadata", {})
        if isinstance(metadata, str) and metadata:
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}
        elif not metadata:
            metadata = {}
        
        result = {
            "text": text_content,
            "title": metadata.get("title"),
            "page": metadata.get("page"),
            "source_uri": metadata.get("source_uri")
        }
        
        # Only add if we have actual text content
        if result["text"]:
            results.append(result)
    
    return results


def search_and_rerank(query: str, top_k: int = 8, rerank_top_n: int = 3) -> tuple[List[Dict], List[float]]:
    """
    Search KB and rerank results using NIM reranker.
    Falls back to original results if reranking fails.
    
    Args:
        query: The search query
        top_k: Number of initial results to retrieve
        rerank_top_n: Number of top results to return after reranking
        
    Returns:
        Tuple of (reranked_results, relevance_scores)
    """
    # Get initial KB results
    kb_results = search_kb(query, top_k)
    
    if not kb_results:
        return [], []
    
    # Extract passages for reranking
    passages = [r.get("text", "") for r in kb_results]
    
    # Try to rerank using NIM
    try:
        rerank_response = rerank(query, passages)
        
        # Parse reranking results and sort by score
        rankings = rerank_response.get("rankings", [])
        
        # Sort by logit and get scores
        sorted_rankings = sorted(rankings, key=lambda x: x.get("logit", 0), reverse=True)[:rerank_top_n]
        
        # Reorder KB results based on reranking
        reranked_results = []
        scores = []
        
        for ranking in sorted_rankings:
            idx = ranking.get("index", 0)
            score = ranking.get("logit", 0)
            
            if idx < len(kb_results):
                reranked_results.append(kb_results[idx])
                scores.append(score)
        
        return reranked_results, scores
        
    except Exception as e:
        # Reranking failed - just return original results with default scores
        print(f"Reranking failed, using original order: {e}")
        top_results = kb_results[:rerank_top_n]
        # Assign descending scores from 1.0
        scores = [1.0 - (i * 0.1) for i in range(len(top_results))]
        return top_results, scores


def insert_chunk(text: str, title: Optional[str] = None, page: Optional[int] = None, 
                 source_uri: Optional[str] = None):
    """
    Insert a chunk of text into the knowledge base.
    
    Args:
        text: The text content to insert
        title: Optional title/heading
        page: Optional page number
        source_uri: Optional source URI/reference
    """
    # MindsDB requires database.table format
    sql = f"INSERT INTO mindsdb.{KB_NAME} (text, title, page, source_uri) VALUES (%s, %s, %s, %s);"
    
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (text, title, page, source_uri))
        conn.commit()

