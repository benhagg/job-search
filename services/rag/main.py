import fastapi

app = fastapi.FastAPI()

@app.get("/health")
def health():
    return {"status": "RAG service is healthy"}, 200

@app.post("/query")
def query(request: fastapi.Request):
    data = request.json()
    
    return {"status": "Query received", "data": data}, 200