import asyncio
import json
import uuid
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any

from engine.research_engine import ResearchEngine
from engine.database import db

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join("static", "index.html"))

@app.get("/api/health")
async def health_check():
    """Dedicated endpoint for UptimeRobot to ping"""
    return {"status": "active", "message": "ScholarFlow is running smoothly"}

engine = ResearchEngine()

# Temporary in-memory store for active tasks.
# In a highly distributed production app, this should be Redis or a DB.
tasks_store: Dict[str, Dict[str, Any]] = {}

class SearchRequest(BaseModel):
    mode: int
    input_data: str
    page: int = 1
    existing_query: str = None
    existing_profile: str = None

class AnalyzeRequest(BaseModel):
    selected_papers: List[Dict[str, Any]]
    profile: str

@app.post("/api/search")
async def api_search(req: SearchRequest):
    results = await engine.discover(
        req.mode, 
        req.input_data, 
        page=req.page, 
        existing_query=req.existing_query, 
        existing_profile=req.existing_profile
    )
    if "error" in results:
        return JSONResponse({"error": results["error"]}, status_code=400)
    return JSONResponse(results)

@app.post("/api/start_analysis")
async def start_analysis(req: AnalyzeRequest):
    task_id = str(uuid.uuid4())
    tasks_store[task_id] = {
        "papers": req.selected_papers,
        "profile": req.profile,
        "status": "pending"
    }
    return JSONResponse({"task_id": task_id})

@app.get("/api/analyze/{task_id}")
async def analyze_stream(task_id: str, request: Request):
    if task_id not in tasks_store:
        return JSONResponse({"error": "Task not found"}, status_code=404)
        
    task_data = tasks_store[task_id]
    papers = task_data["papers"]
    profile = task_data["profile"]

    async def event_generator():
        all_analyses = []
        
        async def yield_cb(msg: str):
            # Send progress updates
            data = json.dumps({"type": "progress", "message": msg})
            yield f"data: {data}\n\n"

        for paper in papers:
            # We must yield from the generator. Since deep_analyze_paper is async,
            # we can pass a callback that appends to a queue, or we can just yield directly
            # by using an async queue.
            # To simplify, we will just use an async queue to bridge the callback and generator.
            pass
            
        # Refactored generator using an async queue
        q = asyncio.Queue()
        
        async def queue_cb(msg: str):
            await q.put({"type": "progress", "message": msg})

        async def process_single_paper(paper):
            analysis = await engine.deep_analyze_paper(
                paper_id=paper.get("external_id", ""),
                title=paper.get("title", ""),
                url=paper.get("url", ""),
                year=paper.get("publication_year", "Unknown"),
                profile=profile,
                yield_callback=queue_cb
            )
            if analysis:
                report = await engine.synthesize_paper(analysis, profile, paper.get("title", ""), yield_callback=queue_cb)
                
                # Update database for this specific paper
                await db.update_deep_analysis(paper.get("external_id", ""), report)
                
                await q.put({
                    "type": "paper_complete", 
                    "external_id": paper.get("external_id", ""), 
                    "report": report
                })

        async def worker():
            try:
                # Run all selected papers in true parallel!
                tasks = [process_single_paper(paper) for paper in papers]
                await asyncio.gather(*tasks)
                
                await q.put({"type": "all_complete"})
            except Exception as e:
                await q.put({"type": "error", "message": str(e)})
            finally:
                await q.put(None) # EOF marker

        # Start the worker task
        asyncio.create_task(worker())

        # Yield events from the queue
        while True:
            # If client disconnects
            if await request.is_disconnected():
                break
                
            item = await q.get()
            if item is None:
                break
            
            yield f"data: {json.dumps(item)}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.on_event("shutdown")
async def shutdown_event():
    await engine.shutdown()
