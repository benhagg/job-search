import fastapi
from fastapi import HTTPException
import pandas as pd
import chromadb

# use pandas to process the Excel data
# columns as defined below
# Title,Employment Type,Employer,Expires,Job Salary,Salary Type,Job Location,Location Type,Residential Address,Job Roles
def clean_data(file: fastapi.UploadFile) -> pd.DataFrame:
    try:
        df = pd.read_excel(file.file)
        file.file.seek(0)  # Reset file pointer to beginning
        from openpyxl import load_workbook
        workbook = load_workbook(file.file)
        sheet = workbook.active
        # Skip the header row (index 0) since pd.read_excel already handles headers
        urls = [cell.hyperlink.target if cell.hyperlink else None for cell in sheet['A'][1:]]
        df["URL"] = urls
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read Excel file: {str(e)}")
    # Example cleaning steps
    df['Expires'] = pd.to_datetime(df['Expires'], errors='coerce')  # Convert to datetime, coerce errors
    df = df.dropna(subset=['Expires'])  # Drop rows where 'Expires' could not be converted
    df = df[df['Expires'] >= pd.Timestamp.now()]  # Keep only rows where 'Expires' is in the future
    return df

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a list of texts using embed container."""
    import os
    import requests

    url = os.getenv("EMBEDDING_URL", "http://embed:8003/embed")
    resp = requests.post(url, json={"texts": texts})
    resp.raise_for_status()
    return resp.json()[0]["embeddings"]

def upload_to_chroma(embeddings: list[list[float]], texts: list[str], metadata: list[dict]):
    """Upload embeddings and texts to ChromaDB."""
    
    client = chromadb.HttpClient(host="chroma", port=8001)
    collection = client.get_or_create_collection(name="job_listings")
    metadata = [{k: str(v) for k, v in meta.items()} for meta in metadata]

    for idx, (text, embedding, meta) in enumerate(zip(texts, embeddings, metadata)):
        doc_id = f"job-{idx}"
        document = {
            "text": text,
            "metadata": meta
        }
        collection.add(
            documents=[document["text"]],
            metadatas=[document["metadata"]],
            ids=[doc_id],
            embeddings=[embedding]
        )