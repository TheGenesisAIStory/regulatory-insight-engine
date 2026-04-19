from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domain_gate import evaluate_domain_gate  # noqa: E402


def test_domain_gate_disabled_passes_ood_query():
    decision = evaluate_domain_gate(
        "Quali ETF UCITS consigli per esporsi ai Treasury USA?",
        enabled=False,
        mode="hybrid",
    )

    assert decision.passed is True
    assert decision.mode == "off"


def test_domain_gate_hybrid_passes_in_domain_query():
    decision = evaluate_domain_gate(
        "Quando si presume SICR secondo IFRS 9?",
        enabled=True,
        mode="hybrid",
    )

    assert decision.passed is True
    assert "sicr" in decision.matched_allow_terms
    assert "ifrs" in decision.matched_allow_terms


def test_domain_gate_hybrid_blocks_plausible_ood_query():
    decision = evaluate_domain_gate(
        "Quali ETF UCITS consigli per esporsi ai Treasury USA a breve termine?",
        enabled=True,
        mode="hybrid",
    )

    assert decision.passed is False
    assert decision.reason == "domain_gate_denied_term"
    assert "etf" in decision.matched_deny_terms


def test_domain_gate_can_load_terms_file(tmp_path):
    terms_path = tmp_path / "terms.json"
    terms_path.write_text(
        json.dumps(
            {
                "allow_terms": ["ifrs"],
                "deny_terms": ["solvency"],
                "extra_allow_terms": ["crr"],
                "extra_deny_terms": ["mifid"],
            }
        ),
        encoding="utf-8",
    )

    allowed = evaluate_domain_gate("Ambito CRR", enabled=True, mode="hybrid", terms_path=terms_path)
    denied = evaluate_domain_gate("Requisiti Solvency II", enabled=True, mode="hybrid", terms_path=terms_path)

    assert allowed.passed is True
    assert denied.passed is False
    assert denied.reason == "domain_gate_denied_term"
