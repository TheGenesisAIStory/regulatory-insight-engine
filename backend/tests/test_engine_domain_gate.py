from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import genisia_rag_engine as rag  # noqa: E402


def high_score_result():
    return [
        rag.SearchResult(
            chunk="Relevant local context",
            source="IFRS9.pdf p. 27",
            score=0.82,
            dense_score=0.8,
            keyword_score=0.9,
        )
    ]


def patch_engine_io(monkeypatch, engine: rag.GenisiaEngine):
    monkeypatch.setattr(engine, "search", lambda query, top_k: high_score_result())
    monkeypatch.setattr(rag, "audit_query", lambda event: None)


def patch_runtime_settings(monkeypatch, enabled: bool):
    monkeypatch.setattr(
        rag,
        "settings",
        SimpleNamespace(
            enable_domain_gate=enabled,
            domain_gate_mode="hybrid",
            domain_gate_terms_path=None,
        ),
    )


def test_engine_score_only_still_answers_when_domain_gate_disabled(monkeypatch):
    engine = rag.GenisiaEngine()
    patch_engine_io(monkeypatch, engine)
    patch_runtime_settings(monkeypatch, enabled=False)
    monkeypatch.setattr(engine, "ask_llm", lambda question, context, model=None: ("Risposta dal contesto", "qwen2.5:3b"))

    response = engine.ask("Quali ETF UCITS consigli?", top_k=1)

    assert response["noAnswer"] is False
    assert response["answer"] == "Risposta dal contesto"
    assert response["reason"] is None


def test_engine_domain_gate_blocks_plausible_ood_before_llm(monkeypatch):
    engine = rag.GenisiaEngine()
    patch_engine_io(monkeypatch, engine)
    patch_runtime_settings(monkeypatch, enabled=True)

    def fail_if_called(question, context, model=None):
        raise AssertionError("LLM should not be called when domain gate blocks the query")

    monkeypatch.setattr(engine, "ask_llm", fail_if_called)

    response = engine.ask("Quali ETF UCITS consigli per esporsi ai Treasury USA?", top_k=1)

    assert response["noAnswer"] is True
    assert response["reason"] == "domain_gate_denied_term"
    assert response["confidence"] == "low"
