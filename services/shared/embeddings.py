from typing import List
import os
from sentence_transformers import SentenceTransformer

_EMBED_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")

# lazy model
_local_model = None

def _load_local_model():
    global _local_model
    if _local_model is None:
        _local_model = SentenceTransformer(_EMBED_MODEL)
    return _local_model

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Return a list of embeddings for the input texts.
    uses local sentence-transformers model.
    """
    # local
    model = _load_local_model()
    emb = model.encode(texts, convert_to_numpy=False)
    # model.encode may return list of numpy arrays — convert to plain lists
    return [list(map(float, e)) for e in emb]