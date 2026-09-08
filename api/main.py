import math
import os
import re
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from youtube_transcript_api import YouTubeTranscriptApi

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

app = FastAPI(title="NOVA API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","), allow_methods=["*"], allow_headers=["*"])


class AskRequest(BaseModel):
    video_id: str = Field(min_length=6, max_length=20)
    question: str = Field(min_length=2, max_length=1000)


def chunks(text: str, size: int = 1200, overlap: int = 200) -> list[str]:
    words = text.split()
    step = max(size // 6 - overlap // 6, 1)
    return [" ".join(words[index:index + size // 6]) for index in range(0, len(words), step)]


def lexical_context(question: str, documents: list[str], limit: int = 4) -> list[str]:
    terms = set(re.findall(r"[a-z0-9]+", question.lower()))
    scored = sorted(((len(terms.intersection(set(re.findall(r"[a-z0-9]+", doc.lower())))), doc) for doc in documents), reverse=True)
    return [doc for score, doc in scored[:limit] if score > 0] or documents[:limit]


def cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    denominator = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return numerator / denominator if denominator else 0


@lru_cache(maxsize=32)
def transcript_for(video_id: str) -> str:
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
        return " ".join(item.text for item in fetched)
    except Exception as error:
        raise HTTPException(status_code=422, detail=f"Transcript unavailable: {error}") from error


def retrieve(question: str, documents: list[str], client: Any) -> list[str]:
    if not client:
        return lexical_context(question, documents)
    embeddings = client.embeddings.create(model="text-embedding-3-small", input=[question, *documents]).data
    query_vector = embeddings[0].embedding
    ranked = sorted(zip((cosine(query_vector, item.embedding) for item in embeddings[1:]), documents), reverse=True)
    return [doc for _, doc in ranked[:4]]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nova-api"}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "NOVA API", "status": "running", "health": "/health", "ask": "/api/ask"}


@app.post("/api/ask")
def ask(request: AskRequest) -> dict[str, Any]:
    transcript = transcript_for(request.video_id)
    documents = chunks(transcript)
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if OpenAI and os.getenv("OPENAI_API_KEY") else None
    context = retrieve(request.question, documents, client)
    if not client:
        return {"answer": f"I found this in the transcript: {context[0][:500]}", "sources": len(context), "mode": "local"}
    context_text = "\n\n".join(context)
    response = client.chat.completions.create(model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"), temperature=0.2, messages=[{"role": "system", "content": "Answer only from the supplied transcript. Say when the transcript does not contain the answer. Be concise and mention uncertainty."}, {"role": "user", "content": f"Transcript context:\n\n{context_text}\n\nQuestion: {request.question}"}])
    return {"answer": response.choices[0].message.content, "sources": len(context), "mode": "openai"}