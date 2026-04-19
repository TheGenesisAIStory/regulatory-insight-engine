#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from audit import logger
from genisia_rag_engine import RagError, engine
from schemas import (
    AskRequest,
    AskResponse,
    DocumentsResponse,
    ErrorResponse,
    ReadinessResponse,
    RebuildRequest,
    RebuildResponse,
    RuntimeStatus,
)


app = FastAPI(
    title="Gen.Is.IA Regulatory RAG API",
    version="0.2.0",
    responses={503: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)

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


def _http_error(exc: Exception, fallback_status: int = 500) -> HTTPException:
    status_code = getattr(exc, "status_code", fallback_status)
    logger.error("api_error status=%s detail=%s", status_code, exc)
    engine.last_error = str(exc)
    return HTTPException(status_code=status_code, detail=str(exc))


@app.get("/health", response_model=RuntimeStatus)
def health():
    return engine.status()


@app.get("/ready", response_model=ReadinessResponse)
def readiness():
    return engine.readiness()


@app.get("/documents", response_model=DocumentsResponse)
def documents():
    return {"documents": engine.documents()}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    try:
        result = engine.ask(payload.question, top_k=payload.topK, model=payload.model)
        result["generatedAt"] = datetime.now().isoformat()
        return result
    except RagError as exc:
        raise _http_error(exc, fallback_status=503) from exc
    except Exception as exc:
        raise _http_error(exc, fallback_status=500) from exc


@app.post("/index/rebuild", response_model=RebuildResponse)
def rebuild(payload: RebuildRequest):
    try:
        engine.initialize(rebuild=True, download=payload.download)
        return {"ok": True, "status": engine.status()}
    except RagError as exc:
        raise _http_error(exc, fallback_status=503) from exc
    except Exception as exc:
        raise _http_error(exc, fallback_status=500) from exc
