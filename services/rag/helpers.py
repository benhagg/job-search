def query(collection_name: str, query_text: str, n_results: int = 15):
    import chromadb
    client = chromadb.HttpClient(host="chroma", port="8001")    
    collection = client.get_collection(collection_name)
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results