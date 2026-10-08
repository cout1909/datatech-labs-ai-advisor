"""Small, build-time FAISS index with local ONNX semantic embeddings."""
import hashlib
import json
import logging
import re
from pathlib import Path
import numpy as np
from app.config import BASE_DIR

logger = logging.getLogger(__name__)
MODEL = "BAAI/bge-small-en-v1.5"
DATA_PATH = BASE_DIR / "app/data/knowledge.json"
INDEX_PATH = BASE_DIR / "index"
STOPWORDS = set("a an the our we to of and or in on for with from is are need want have this that it as be can by company business".split())

def tokens(text):
    return set(re.findall(r"[a-z]{3,}", text.lower())) - STOPWORDS

def document_text(doc):
    return f"{doc['title']}. {doc['description']} Use cases: {', '.join(doc['use_cases'])}."

def load_embedder(local_only=False):
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=MODEL, cache_dir=str(INDEX_PATH / "models"),
                         threads=1, local_files_only=local_only)

def build_index():
    import faiss
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    documents = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    chunks = [{"document_id": doc["id"], "chunk_id": f"{doc['id']}:{i}", "text": chunk}
              for doc in documents for i, chunk in enumerate(splitter.split_text(document_text(doc)))]
    INDEX_PATH.mkdir(parents=True, exist_ok=True)
    model = load_embedder()
    vectors = np.array(list(model.embed([c["text"] for c in chunks])), dtype="float32")
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(INDEX_PATH / "services.faiss"))
    (INDEX_PATH / "metadata.json").write_text(json.dumps({
        "model": MODEL, "data_sha256": hashlib.sha256(DATA_PATH.read_bytes()).hexdigest(),
        "chunks": chunks}), encoding="utf-8")
    print(f"Built {len(chunks)} chunks; {vectors.shape[1]}-dimensional semantic embeddings.")

class Retriever:
    def __init__(self, initialize_vector=True):
        self.documents = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        self.mode = "keyword_fallback"
        self.index = self.embedder = None
        if initialize_vector:
            try:
                import faiss
                metadata = json.loads((INDEX_PATH / "metadata.json").read_text(encoding="utf-8"))
                if metadata["data_sha256"] != hashlib.sha256(DATA_PATH.read_bytes()).hexdigest() or metadata["model"] != MODEL:
                    raise ValueError("Index is stale; rebuild it")
                self.chunks = metadata["chunks"]
                self.index = faiss.read_index(str(INDEX_PATH / "services.faiss"))
                self.embedder = load_embedder(local_only=True)
                self.mode = "vector"
            except Exception as exc:
                logger.warning("Vector initialization failed (%s); using keyword fallback", type(exc).__name__)

    def search(self, query, limit=3):
        if self.mode == "vector":
            try:
                import faiss
                vector = np.array(list(self.embedder.query_embed(query)), dtype="float32")
                faiss.normalize_L2(vector)
                scores, positions = self.index.search(vector, self.index.ntotal)
                ids = []
                matched_chunks = {}
                for score, pos in zip(scores[0], positions[0]):
                    if pos < 0 or score < 0.58:
                        continue
                    doc_id = self.chunks[int(pos)]["document_id"]
                    if doc_id not in ids:
                        ids.append(doc_id)
                        matched_chunks[doc_id] = self.chunks[int(pos)]
                by_id = {d["id"]: d for d in self.documents}
                return [dict(by_id[i], chunk_id=matched_chunks[i]['chunk_id'], retrieved_text=matched_chunks[i]['text']) for i in ids[:limit]], "vector"
            except Exception as exc:
                logger.warning("Vector query failed (%s); using keyword fallback", type(exc).__name__)
        query_tokens = tokens(query)
        ranked = sorted(((len(query_tokens & tokens(document_text(d))), d) for d in self.documents),
                        key=lambda item: (-item[0], item[1]["id"]))
        return [dict(d, chunk_id=f"{d['id']}:document", retrieved_text=document_text(d)) for score, d in ranked if score > 0][:limit], "keyword_fallback"

if __name__ == "__main__":
    build_index()
