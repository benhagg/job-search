import fastapi
from fastapi.middleware.cors import CORSMiddleware
from helpers import query
import websockets
import json

import debugpy
import httpx
debugpy.listen(("0.0.0.0", 5678))  # Use a unique port per service if debugging all at once
print("Waiting for debugger attach...")
# debugpy.wait_for_client()  # Optional: pause until debugger attaches

app = fastapi.FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "RAG service is healthy"}, 200

@app.post("/search")
async def search(request: fastapi.Request):
    data = await request.json()
    n_results = data.get("n_results", 5)
    results = query("job_listings", data["query"], n_results=n_results)
    if not results:
        return {"status": "No results found"}, 404
    if data["use_ai"]:
        prompt = f"Based on the attached job listings and Query, rank the {n_results} Job Listings in order from most to least relevant and explain why they are a good fit \n\n Query: {data['query']} \n Job Listings: {results['metadatas']}"
        LLM_URL = "http://llm:7860/generate"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(LLM_URL, json={"prompt": prompt}, timeout=150.0)
                resp.raise_for_status()
                ai_response = resp.text
        except Exception as e:
            return {"status": "Error occurred with LLM connection", "error": str(e), "results": results}, 500
        return {"status": "Query processed with AI", "data": data, "results": results, "ai_response": ai_response}, 200
    else:
        return {"status": "Query received", "data": data, "results": results}, 200