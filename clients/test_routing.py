#!/usr/bin/env python3
"""
Test script for the intelligent query routing system.

Usage:
    python clients/test_routing.py
"""

import requests
import json
import time
from typing import Literal

BASE_URL = "http://localhost:8080"


def color_print(text: str, color: str = "white"):
    """Print colored text"""
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "red": "\033[91m",
        "white": "\033[0m",
        "cyan": "\033[96m",
        "magenta": "\033[95m"
    }
    print(f"{colors.get(color, '')}{text}\033[0m")


def health_check():
    """Check system health"""
    color_print("\n=== System Health Check ===", "cyan")
    
    endpoints = [
        "/health/llm",
        "/health/rerank",
        "/health/kb",
        "/api/query/health"
    ]
    
    all_healthy = True
    for endpoint in endpoints:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if resp.ok:
                color_print(f"✓ {endpoint}: OK", "green")
            else:
                color_print(f"✗ {endpoint}: {resp.status_code}", "red")
                all_healthy = False
        except Exception as e:
            color_print(f"✗ {endpoint}: {str(e)}", "red")
            all_healthy = False
    
    return all_healthy


def test_query(
    query: str,
    override: Literal["force:kb", "force:research", None] = None,
    depth: str = "quick",
    expected_route: str = None
):
    """Test a query and display results"""
    
    color_print(f"\n{'='*60}", "blue")
    color_print(f"Query: {query}", "yellow")
    if override:
        color_print(f"Override: {override}", "magenta")
    color_print(f"{'='*60}", "blue")
    
    payload = {
        "query": query,
        "depth": depth
    }
    if override:
        payload["override"] = override
    
    try:
        start_time = time.time()
        resp = requests.post(
            f"{BASE_URL}/api/query",
            json=payload,
            timeout=300
        )
        elapsed = time.time() - start_time
        
        if not resp.ok:
            color_print(f"Error: {resp.status_code} - {resp.text}", "red")
            return False
        
        result = resp.json()
        
        # Display results
        color_print(f"\nRoute Taken: {result['route_taken']}", "cyan")
        color_print(f"Confidence: {result.get('confidence', 'N/A')}", "cyan")
        color_print(f"Research Conducted: {result['research_conducted']}", "cyan")
        color_print(f"Response Time: {elapsed:.2f}s", "cyan")
        
        color_print(f"\nAnswer:", "green")
        print(result['answer'][:500] + "..." if len(result['answer']) > 500 else result['answer'])
        
        color_print(f"\nSources ({len(result['sources'])}):", "yellow")
        for i, source in enumerate(result['sources'][:3], 1):
            print(f"  [{i}] {source.get('title', 'N/A')} - {source.get('source_uri', 'N/A')}")
            if source.get('relevance_score'):
                print(f"      Relevance: {source['relevance_score']:.3f}")
        
        # Verify expected route
        if expected_route and result['route_taken'] != expected_route:
            color_print(f"⚠️  Expected route '{expected_route}' but got '{result['route_taken']}'", "yellow")
        else:
            color_print("✓ Test passed", "green")
        
        return True
        
    except Exception as e:
        color_print(f"Exception: {str(e)}", "red")
        return False


def main():
    """Run test suite"""
    color_print("\n" + "="*60, "cyan")
    color_print("KB Agent Routing System - Test Suite", "cyan")
    color_print("="*60 + "\n", "cyan")
    
    # Health check
    if not health_check():
        color_print("\n⚠️  Some health checks failed. Continuing anyway...\n", "yellow")
    
    # Test 1: Force KB only
    color_print("\n\n### Test 1: Force KB Only ###", "magenta")
    test_query(
        query="What is in our knowledge base about agent routing?",
        override="force:kb"
        # Expected: Should only search KB, no research
    )
    
    time.sleep(2)
    
    # Test 2: Force Research
    color_print("\n\n### Test 2: Force Research ###", "magenta")
    test_query(
        query="How does a Large Language Model work? What is the architecture of a Large Language Model? What is attention?",
        override="force:research",
        depth="deep",
        expected_route="research_only"
    )
    
    time.sleep(2)
    
    # Test 3: Smart routing (likely KB)
    color_print("\n\n### Test 3: Smart Routing (KB expected) ###", "magenta")
    test_query(
        query="agent routing architecture",
        depth="deep",
        # Expected: Should find results from previous research in KB
    )
    
    time.sleep(2)
    
    # Test 4: Smart routing (likely Research)
    color_print("\n\n### Test 4: Smart Routing (Research expected) ###", "magenta")
    test_query(
        query="What happened in the AI research community in the last 24 hours?",
        depth="deep"
        # Expected: Very recent info, should trigger research
    )
    
    color_print("\n\n" + "="*60, "cyan")
    color_print("Test Suite Complete!", "cyan")
    color_print("="*60 + "\n", "cyan")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        color_print("\n\nTest interrupted by user", "yellow")

