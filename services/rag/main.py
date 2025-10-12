import fastapi
from fastapi.middleware.cors import CORSMiddleware
from helpers import query

import debugpy
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
        # ai processing of results here
        return {"status": "AI processing not implemented yet", "data": data, "results": results}, 501
    else:
        return {"status": "Query received", "data": data, "results": results}, 200