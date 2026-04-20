from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import api  # noqa: E402


def runtime_status(**overrides):
    status = {
        "ready": True,
        "ollamaOnline": True,
        "baseDir": "/tmp/rag",
        "docsDir": "/tmp/rag/normativa",
        "cacheFile": "/tmp/rag/genisia_embeddings_cache.pkl",
        "cacheExists": True,
        "documents": 1,
        "chunks": 12,
        "embedModel": "embeddinggemma",
        "chatModel": "qwen2.5:3b",
        "activeChatModel": "qwen2.5:3b",
        "availableModels": ["qwen2.5:3b", "embeddinggemma:latest"],
        "categories": ["ifrs9"],
        "domainGate": {"enabled": False, "mode": "hybrid", "termsPath": None},
        "error": None,
    }
    status.update(overrides)
    return status


class FakeEngine:
    last_error = None

    def status(self):
        return runtime_status()

    def readiness(self):
        return {
            "ready": True,
            "checks": {
                "ollama": True,
                "documents": True,
                "cache": True,
                "index": True,
                "chatModel": True,
                "embedModel": True,
            },
            "status": runtime_status(),
            "reasons": [],
        }

    def documents(self):
        return [
            {
                "id": "IFRS9",
                "title": "IFRS9",
                "source": "ifrs9",
                "pages": 0,
                "chunks": 12,
                "status": "indexed",
                "updated": 1776534648.0,
                "filename": "IFRS9.pdf",
            }
        ]

    def ask(self, question: str, top_k: int, model: str | None = None):
        return {
            "question": question,
            "answer": "Non ho trovato un contesto abbastanza affidabile nei documenti indicizzati.",
            "model": model or "qwen2.5:3b",
            "confidence": "low",
            "sources": [],
            "noAnswer": True,
            "reason": "retrieval_score_below_threshold",
            "durationMs": 7,
        }

    def initialize(self, rebuild: bool = False, download: bool = True):
        return None

    def preload_if_available(self):
        return True


def client(monkeypatch):
    monkeypatch.setattr(api, "engine", FakeEngine())
    return TestClient(api.app)


def test_health_serializes_runtime_status(monkeypatch):
    response = client(monkeypatch).get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["ollamaOnline"] is True
    assert data["activeChatModel"] == "qwen2.5:3b"
    assert data["chunks"] == 12


def test_readiness_reports_checks(monkeypatch):
    response = client(monkeypatch).get("/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True
    assert data["checks"]["index"] is True
    assert data["reasons"] == []


def test_ask_no_answer_contract(monkeypatch):
    response = client(monkeypatch).post(
        "/ask",
        json={"question": "Domanda fuori contesto", "topK": 3, "model": "qwen2.5:3b"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["noAnswer"] is True
    assert data["reason"] == "retrieval_score_below_threshold"
    assert data["confidence"] == "low"
    assert data["sources"] == []
    assert "generatedAt" in data
    assert data["durationMs"] == 7


def test_documents_response_serializes(monkeypatch):
    response = client(monkeypatch).get("/documents")

    assert response.status_code == 200
    data = response.json()
    assert data["documents"][0]["filename"] == "IFRS9.pdf"
    assert data["documents"][0]["status"] == "indexed"
