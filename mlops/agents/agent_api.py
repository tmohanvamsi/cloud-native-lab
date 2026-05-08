"""
Day 10 — FastAPI wrapper around the DevOps agent for K8s deployment.
Exposes /health and /ask endpoints so the agent runs as a service.
"""
import ollama
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="DevOps AI Agent API", version="1.0.0")

OLLAMA_HOST = "http://ollama:11434"   # points to Ollama service in cluster


class Query(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "devops-agent"}


@app.post("/ask")
def ask(query: Query):
    """Send a DevOps question to the LLM and get an answer."""
    client = ollama.Client(host=OLLAMA_HOST)
    response = client.chat(
        model="llama3",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a DevOps AI assistant. Answer infrastructure and "
                    "Kubernetes questions concisely and accurately."
                ),
            },
            {"role": "user", "content": query.question},
        ],
    )
    return {
        "question": query.question,
        "answer":   response["message"]["content"],
    }
