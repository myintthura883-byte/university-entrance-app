# app.py (Complete Refactored Version)
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, Response
import os
import json
import requests
from werkzeug.utils import secure_filename

# Import all modular components
from src.config_loader import load_config
from src.llm_model import get_ollama_llm
from src.embedding_model import get_ollama_embeddings # Needed for vector store connection
from src.vector_store import get_chroma_vector_store
from src.rag_chain import build_rag_chain

# --- Load Configuration (cached to run once) ---
config = load_config()
app_name = config['app_name']
ollama_config = config['ollama']
vector_store_config = config['data_ingestion']['vector_store']
rag_config = config['rag']

# --- Initialize Flask ---
app = Flask(__name__)
app.secret_key = "Oxygen200373#"  # for session


# --- Setup RAG system ---
llm = get_ollama_llm(
    model_name=ollama_config['llm_model'],
    base_url=ollama_config['host']
)
    
# 2. Initialize Embedding Model (for connecting to ChromaDB)
embeddings = get_ollama_embeddings(
    model_name=ollama_config['embedding_model'],
    base_url=ollama_config['host']
)
if not os.path.exists(vector_store_config['persist_directory']):
    raise FileNotFoundError("Run `prep_data.py` to ingest documents into ChromaDB first.")

# 3. Connect to ChromaDB
# Ensure ChromaDB directory exists
if not os.path.exists(vector_store_config['persist_directory']):
    raise FileNotFoundError(f"ChromaDB directory not found: {vector_store_config['persist_directory']}")

vector_db = get_chroma_vector_store(
    persist_directory=vector_store_config['persist_directory'],
    collection_name=vector_store_config['collection_name'],
    embedding_function=embeddings
)
    
# Get retriever from vector store
retriever = vector_db.as_retriever(search_kwargs={"k": rag_config['retrieval_k']})


# 4. Build RAG chain
rag_chain = build_rag_chain(
    llm=llm,
    retriever=retriever,
    chain_type=rag_config['chain_type'],
    return_source_documents=True
)

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def chat():
    if "messages" not in session:
        session["messages"] = []
    

    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()
        session["messages"].append({"role": "user", "content": prompt})
        

        # Handle greetings
        if prompt.lower() in ["hi", "hello", "hey", "မင်္ဂလာပါ"]:
            session["messages"].append({"role": "assistant", "content": "Hello! How can I assist you today?"})
            print("[DEBUG] Added greeting assistant response.")
            return redirect(url_for("chat"))

        try:
            
            result = rag_chain.invoke({"query": prompt})
            

            result = rag_chain.invoke({"query": prompt})
            response_content = result.get("result", "No answer.")
            


            source_documents = result.get("source_documents", [])
            final_reply = response_content

            if source_documents:
                final_reply += "\n\nSources:\n"
                for i, doc in enumerate(source_documents):
                    name = doc.metadata.get("source", doc.metadata.get("file_path", f"Document {i+1}"))
                    page = doc.metadata.get("page", None)
                    if page:
                        name += f" (Page: {page})"
                    final_reply += f"- {name}\n"
            full_responese += response_content + final_reply
        except Exception as e:
            
            full_responese= f"Error: {e}"

        session["messages"].append({"role": "assistant", "content": full_responese})
        return redirect(url_for("index"))

    return render_template("chat.html", app_name=app_name, messages=session["messages"])


@app.route("/chat-stream", methods=["POST"])
def chat_stream():
    data = request.json
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    def generate():
        # Instead of rag_chain.invoke, simulate streaming or use your actual streaming method here.
        # For example, yield partial pieces of the response in a loop.
        # Here is a dummy example for demonstration:
        try:
            # Replace this block with your real LLM streaming logic
            result = rag_chain.invoke({"query": prompt})

            if isinstance(result, dict) and "result" in result:
                response_content = result["result"]
            else:
                response_content = str(result)

            # Yield in chunks (simulate streaming)
            for chunk in response_content.split('. '):  # naive chunking by sentences
                yield chunk.strip() + '. '
        except Exception as e:
            yield f"Error: {e}"

    return Response(generate(), content_type="text/plain")

# Route to reset chat session
@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("chat"))

if __name__ == "__main__":
    app.run(debug=True)
