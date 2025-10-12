import fastapi
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from helpers import embed_texts, clean_data, upload_to_chroma


# For debugging
import debugpy
debugpy.listen(("0.0.0.0", 5679))  # Use a unique port per service if debugging all at once
print("Waiting for debugger attach...")
debugpy.wait_for_client()  # Optional: pause until debugger attaches

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


@app.post("/add-csv")
def add_csv(file: fastapi.UploadFile):
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV file: {str(e)}")
    try:
        df = clean_data(df)
        texts = df.apply(
            lambda row: f"{row['Title']}. {row['Employment Type']}. {row['Employer']}. {row['Job Salary']}. {row['Salary Type']}. {row['Job Location']}. {row['Location Type']}. {row['Job Roles']}",
            axis=1
        )
        embeddings = embed_texts(texts.tolist())
        upload_to_chroma(embeddings, texts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV data: {str(e)}")
    return {"status": "CSV file data added successfully"}, 201

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
        upload_to_chroma(embeddings, texts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing JSON data: {str(e)}")
    return {"status": "JSON data added successfully"}, 201
