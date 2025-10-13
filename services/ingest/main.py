import fastapi
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from helpers import embed_texts, clean_data, upload_to_chroma


# For debugging
import debugpy
debugpy.listen(("0.0.0.0", 5679))  # Use a unique port per service if debugging all at once
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
    return {"status": "Ingest service is healthy"}, 200


@app.post("/add-excel")
def add_excel(file: fastapi.UploadFile):
    
    try:
        df = clean_data(file)
        texts = df.apply(
            lambda row: f'{row["Title"]} {row["Employment Type"]}',
            axis=1
        )
        embeddings = embed_texts(texts.tolist())
        # Prepare metadata for each row
        metadata = df[["Title", "Employment Type", "Employer", "Job Salary", "Salary Type", "Job Location", "Location Type", "Job Roles", "URL"]].to_dict(orient="records")
        upload_to_chroma(embeddings, texts.tolist(), metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Excel data: {str(e)}")
    return {"status": "Excel file data added successfully"}, 201

@app.post("/add-json")
async def add_json(request: fastapi.Request):
    import json
    try:
        data = await request.json()
        if not isinstance(data, list):
            raise HTTPException(status_code=400, detail="Expected a list of job listings")
        # Process data
        texts = [
            f"{item['Title']}. {item['Employment Type']}. {item['Employer']}. {item['Job Salary']}. {item['Salary Type']}. {item['Job Location']}. {item['Location Type']}. {item['Job Roles']}"
            for item in data
        ]
        embeddings = embed_texts(texts)
        # Use the original data as metadata
        metadata = [{"source": "json_upload", **item} for item in data]
        upload_to_chroma(embeddings, texts, metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing JSON data: {str(e)}")
    return {"status": "JSON data added successfully"}, 201
