from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ALLOW_TERMS = {
    "banca", "bancaria", "banche", "banking", "basel", "basilea", "capital",
    "capitale", "circ", "circolare", "credito", "creditizi", "creditizio",
    "crr", "default", "ecl", "eba", "esposizione", "esposizioni", "ifrs",
    "impairment", "prudenziale", "regulation", "requirements", "rischio",
    "sicr", "stage", "vigilanza",
}

DEFAULT_DENY_TERMS = {
    "antiriciclaggio", "aml", "carbonara", "covered", "customer", "dcf",
    "disclosure", "disclosures", "duration", "esenzioni", "etf", "fed",
    "ftse", "gdpr", "mifid", "nba", "polizza", "pos", "psd2", "retail",
    "sfdr", "smart", "solvency", "suitability", "swot", "tassazione",
    "treasury", "ucits", "unibanca", "unicredit", "unit", "wacc",
}


@dataclass(frozen=True)
class DomainGateDecision:
    passed: bool
    reason: str | None = None
    mode: str = "off"
    matched_allow_terms: tuple[str, ...] = ()
    matched_deny_terms: tuple[str, ...] = ()


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-ZÀ-ÿ0-9]{3,}", text.lower()))


def load_terms(path: Path | None) -> tuple[set[str], set[str]]:
    allow_terms = set(DEFAULT_ALLOW_TERMS)
    deny_terms = set(DEFAULT_DENY_TERMS)

    if not path:
        return allow_terms, deny_terms

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if "allow_terms" in payload:
        allow_terms = {term.lower() for term in payload["allow_terms"]}
    if "deny_terms" in payload:
        deny_terms = {term.lower() for term in payload["deny_terms"]}
    if "extra_allow_terms" in payload:
        allow_terms.update(term.lower() for term in payload["extra_allow_terms"])
    if "extra_deny_terms" in payload:
        deny_terms.update(term.lower() for term in payload["extra_deny_terms"])

    return allow_terms, deny_terms


def evaluate_domain_gate(
    query: str,
    *,
    enabled: bool,
    mode: str,
    terms_path: Path | None = None,
) -> DomainGateDecision:
    if not enabled:
        return DomainGateDecision(passed=True, mode="off")

    normalized_mode = mode.lower()
    if normalized_mode not in {"denylist", "allowlist", "hybrid"}:
        raise ValueError("DOMAIN_GATE_MODE must be one of: denylist, allowlist, hybrid")

    terms = tokenize(query)
    allow_terms, deny_terms = load_terms(terms_path)
    matched_allow = tuple(sorted(terms & allow_terms))
    matched_deny = tuple(sorted(terms & deny_terms))

    if normalized_mode in {"denylist", "hybrid"} and matched_deny:
        return DomainGateDecision(
            passed=False,
            reason="domain_gate_denied_term",
            mode=normalized_mode,
            matched_allow_terms=matched_allow,
            matched_deny_terms=matched_deny,
        )

    if normalized_mode in {"allowlist", "hybrid"} and not matched_allow:
        return DomainGateDecision(
            passed=False,
            reason="domain_gate_missing_allowed_term",
            mode=normalized_mode,
            matched_allow_terms=matched_allow,
            matched_deny_terms=matched_deny,
        )

    return DomainGateDecision(
        passed=True,
        mode=normalized_mode,
        matched_allow_terms=matched_allow,
        matched_deny_terms=matched_deny,
    )
