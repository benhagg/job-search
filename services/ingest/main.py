import fastapi
import pandas as pd
from data_processing import clean_data

app = fastapi.FastAPI()

@app.get("/health")
def health():
    return {"status": "Ingest service is healthy"}, 200

@app.post("/add-csv")
def add_csv(file: fastapi.UploadFile):
    # process with pandas
    df = pd.read_csv(file.file)
    # clean data
    from data_processing import clean_data
    df = clean_data(df)
    # Title,Employment Type,Employer,Expires,Job Salary,Salary Type,Job Location,Location Type,Residential Address,Job Roles
    

    # convert to embeddings
    return {"status": "CSV file data added successfully"}, 201
