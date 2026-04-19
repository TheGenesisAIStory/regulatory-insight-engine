#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from genisia_rag_engine import TOP_K, engine


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    topK: int = Field(default=TOP_K, ge=1, le=20)
    model: Optional[str] = None


class RebuildRequest(BaseModel):
    download: bool = True


app = FastAPI(title="Gen.Is.IA Regulatory RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return engine.status()


@app.get("/documents")
def documents():
    return {"documents": engine.documents()}


@app.post("/ask")
def ask(payload: AskRequest):
    try:
        result = engine.ask(payload.question, top_k=payload.topK, model=payload.model)
        result["generatedAt"] = datetime.now().isoformat()
        return result
    except Exception as exc:
        engine.last_error = str(exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/index/rebuild")
def rebuild(payload: RebuildRequest):
    try:
        engine.initialize(rebuild=True, download=payload.download)
        return {"ok": True, "status": engine.status()}
    except Exception as exc:
        engine.last_error = str(exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
