import streamlit as st
import chromadb, ollama
from sentence_transformers import SentenceTransformer

st.set_page_config(page_title="Scottish Law AI", page_icon="⚖️", layout="centered")
st.title("⚖️ Scottish Law AI")
st.caption("Ask questions about Scottish legislation and case law. Not a substitute for legal advice.")

@st.cache_resource
def load_resources():
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=r"C:\Users\bhumb\scottish-law-ai\models\scottish_law_db")
    collection = client.get_collection("scottish_law")
    return embedder, collection

embedder, collection = load_resources()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if question := st.chat_input("Ask a question about Scottish law..."):
    st.session_state.messages.append({"role":"user","content":question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching Scottish law..."):
            embedding = embedder.encode(question).tolist()
            results = collection.query(query_embeddings=[embedding], n_results=5)
            context = "\n\n---\n\n".join(results["documents"][0])
            sources = list(set([r["source"] for r in results["metadatas"][0]]))

            prompt = f"""You are a Scottish law assistant. Only answer using the legal text provided below. If the text does not contain a clear answer to the question, say "I don't have enough Scottish legal data to answer this accurately. Please consult a solicitor or visit mygov.scot." Do not guess or fill in gaps from general knowledge. Always end with: This is not legal advice. Please consult a qualified Scottish solicitor.
Always end with: This is not legal advice. Please consult a qualified Scottish solicitor.

SCOTTISH LEGAL TEXT:
{context}

QUESTION: {question}
ANSWER:"""

            response = ollama.chat(model="phi3", messages=[{"role":"user","content":prompt}])
            answer = response["message"]["content"]
            st.write(answer)
            with st.expander("Sources consulted"):
                for s in sources:
                    st.text(s)

    st.session_state.messages.append({"role":"assistant","content":answer})
