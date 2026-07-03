import chromadb, ollama, sys
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="models/scottish_law_db")
collection = client.get_collection("scottish_law")

def ask(question):
    embedding = embedder.encode(question).tolist()
    results = collection.query(query_embeddings=[embedding], n_results=5)
    context = "\n\n---\n\n".join(results["documents"][0])
    sources = list(set([r["source"] for r in results["metadatas"][0]]))

    prompt = f"""You are a Scottish law assistant. Answer the question below using only the legal text provided. 
If the answer is not in the text, say so clearly. Always note that this is not legal advice.

SCOTTISH LEGAL TEXT:
{context}

QUESTION: {question}

ANSWER:"""

    print(f"\nSearching Scottish law for: {question}\n")
    response = ollama.chat(model="phi3", messages=[{"role":"user","content":prompt}])
    answer = response["message"]["content"]
    print(answer)
    print(f"\nSources consulted: {', '.join(sources)}")
    return answer

if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Ask a question about Scottish law: ")
    ask(question)