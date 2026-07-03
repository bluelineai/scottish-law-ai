import os, chromadb
from sentence_transformers import SentenceTransformer

FOLDERS = ["data/legislation", "data/caselaw"]
DB_PATH = "models/scottish_law_db"

print("Loading embedding model...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection("scottish_law")

def chunk_text(text, size=500, overlap=50):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+size])
        chunks.append(chunk)
        i += size - overlap
    return chunks

total = 0
for folder in FOLDERS:
    if not os.path.exists(folder):
        print(f"Folder not found, skipping: {folder}")
        continue
    # Accept .txt, .md, and .html files
    files = [f for f in os.listdir(folder) 
             if f.endswith(".txt") or f.endswith(".md") or f.endswith(".html")]
    print(f"\nProcessing {len(files)} files from {folder}")
    for fname in files:
        path = os.path.join(folder, fname)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            doc_id = f"{fname}_{i}"
            embedding = embedder.encode(chunk).tolist()
            collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"source": fname, "chunk": i}]
            )
            total += 1
        print(f"  Indexed: {fname[:60]} ({len(chunks)} chunks)")

print(f"\nDone. {total} chunks stored in {DB_PATH}")