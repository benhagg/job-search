import fastapi
from fastapi import HTTPException
import pandas as pd
import chromadb

embedColumns = ["Title", "Employment Type"]
metadataColumns = ["Title", "Employment Type", "Employer", "Job Salary", "Salary Type", "Job Location", "Location Type", "Job Roles", "URL"]
# embedColumnsRename = ["Position Title", "Qualifications"]
# metadataColumnsRename = ["Position Title", "Qualifications", "Employer", "Salary", "Salary Type", "Location", "Location Type", "URL"]
# use pandas to process the Excel data
# columns as defined below
# Title,Employment Type,Employer,Expires,Job Salary,Salary Type,Job Location,Location Type,Residential Address,Job Roles
def clean_data(file: fastapi.UploadFile) -> pd.DataFrame:
    # this works for BYU handshake job lists
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

def clean_csv_data(file: fastapi.UploadFile) -> pd.DataFrame:
    """
    Read a CSV uploaded file and normalize column names to the canonical schema used
    by the ingest pipeline so the same embed_texts/upload_to_chroma functions work
    for both Excel and CSV inputs.

    Mapping decisions:
      - "Position Title" -> "Title"
      - "Work Model" -> "Employment Type" (and infer Location Type)
      - "Company" -> "Employer"
      - "Salary" -> "Job Salary" (infer Salary Type when possible)
      - "Location" -> "Job Location"
      - "Qualifications" -> "Job Roles"
      - "Apply" -> "URL"
      - "Date" -> used to compute an "Expires" column (Date + 90 days)
    """
    try:
        file.file.seek(0)
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV file: {str(e)}")

    # canonical target columns expected elsewhere in the pipeline
    target_cols = set(metadataColumns + ["Expires"])

    # helper to safely get a column value or None
    def col_or_none(df, col):
        return df[col] if col in df.columns else None

    # rename map from known CSV headers to canonical names
    rename_map = {}
    if "Position Title" in df.columns:
        rename_map["Position Title"] = "Title"
    if "Work Model" in df.columns:
        rename_map["Work Model"] = "Employment Type"
    if "Company" in df.columns:
        rename_map["Company"] = "Employer"
    if "Salary" in df.columns:
        rename_map["Salary"] = "Job Salary"
    if "Location" in df.columns:
        rename_map["Location"] = "Job Location"
    if "Qualifications" in df.columns:
        rename_map["Qualifications"] = "Job Roles"
    if "Apply" in df.columns:
        rename_map["Apply"] = "URL"

    # apply renames
    if rename_map:
        df = df.rename(columns=rename_map)

    # Infer Expires from Date column if present (assume postings expire after 90 days)
    if "Date" in df.columns and "Expires" not in df.columns:
        try:
            posted = pd.to_datetime(df["Date"], errors="coerce")
            df["Expires"] = posted + pd.Timedelta(days=90)
        except Exception:
            df["Expires"] = pd.NaT

    # Ensure all metadataColumns exist; fill missing with None/empty string
    for col in metadataColumns:
        if col not in df.columns:
            df[col] = None

    # Infer Location Type from Employment Type / Work Model content if possible
    if "Employment Type" in df.columns:
        def infer_location_type(val):
            if pd.isna(val):
                return None
            s = str(val).lower()
            if "remote" in s:
                return "Remote"
            if "hybrid" in s:
                return "Hybrid"
            if "onsite" in s or "on-site" in s or "on site" in s:
                return "Onsite"
            return None
        df["Location Type"] = df.get("Location Type", None)
        df["Location Type"] = df.apply(
            lambda r: r["Location Type"] if pd.notna(r["Location Type"]) else infer_location_type(r.get("Employment Type")),
            axis=1
        )

    # Infer Salary Type from Job Salary string when possible
    if "Job Salary" in df.columns:
        def infer_salary_type(val):
            if pd.isna(val):
                return None
            s = str(val).lower()
            if "/yr" in s or "per year" in s or "year" in s or "annum" in s:
                return "Yearly"
            if "/hr" in s or "per hour" in s or "hour" in s:
                return "Hourly"
            return None
        df["Salary Type"] = df.get("Salary Type", None)
        df["Salary Type"] = df.apply(
            lambda r: r["Salary Type"] if pd.notna(r["Salary Type"]) else infer_salary_type(r.get("Job Salary")),
            axis=1
        )

    # Final cleaning: parse Expires, drop rows without Expires (consistent with Excel handler)
    df["Expires"] = pd.to_datetime(df["Expires"], errors="coerce")
    df = df.dropna(subset=["Expires"])
    df = df[df["Expires"] >= pd.Timestamp.now()]

    # Keep only canonical columns (plus Expires) in a stable order
    out_cols = metadataColumns + ["Expires"]
    df = df[[c for c in out_cols if c in df.columns]]

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