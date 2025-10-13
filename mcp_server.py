import os
import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from gpt_researcher import GPTResearcher

app = FastAPI(title="GPT-Researcher MCP Server")

class ResearchRequest(BaseModel):
    query: str
    depth: str = "deep"
    max_results: int = 12

class ResearchResponse(BaseModel):
    report: str
    query: str
    citations: list = []

@app.post("/research")
async def research(request: ResearchRequest):
    """Conduct research on a given query using GPT-Researcher"""
    try:
        researcher = GPTResearcher(query=request.query, report_type='research_report')
        report = await researcher.conduct_research()
        
        return ResearchResponse(
            report=report,
            query=request.query,
            citations=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conducting research: {str(e)}")

@app.get("/sse")
async def sse_endpoint():
    """SSE endpoint for MCP compatibility"""
    async def event_generator():
        yield f"data: {json.dumps({'type': 'connected', 'message': 'MCP Server Ready'})}\n\n"
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gpt-researcher-mcp"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
