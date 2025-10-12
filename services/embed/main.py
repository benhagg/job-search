import fastapi
from embeddings import embed_texts

import debugpy
debugpy.listen(("0.0.0.0", 5680))  # Use a unique port per service if debugging all at once
print("Waiting for debugger attach...")
# debugpy.wait_for_client()  # Optional: pause until debugger attaches

app = fastapi.FastAPI()

@app.get("/health")
def health():
    return {"status": "Embed service is healthy"}, 200

@app.post("/embed")
async def embed(request: fastapi.Request):
    data = await request.json()
    texts = data.get("texts", [])
    if not texts or not isinstance(texts, list):
        return fastapi.HTTPException(status_code=400, detail="Invalid input: 'texts' must be a non-empty list.")
    embeddings = embed_texts(texts)
    return {"embeddings": embeddings}, 200