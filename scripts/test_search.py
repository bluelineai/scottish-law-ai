import chromadb
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="models/scottish_law_db")
collection = client.get_collection("scottish_law")

query = "What are the rules around land ownership in Scotland?"
embedding = embedder.encode(query).tolist()

results = collection.query(query_embeddings=[embedding], n_results=3)

print(f"Query: {query}\n")
for i, doc in enumerate(results["documents"][0]):
    source = results["metadatas"][0][i]["source"]
    print(f"Result {i+1} (from {source}):")
    print(doc[:300])
    print("---")