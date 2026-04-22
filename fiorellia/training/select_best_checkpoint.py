#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


THRESHOLDS = {
    "in_scope_grounded": 0.80,
    "unsupported_abstention": 0.90,
    "out_of_scope_refusal": 0.95,
    "citation_fidelity": 0.85,
    "italian_regulatory_style": 0.85,
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def candidate_score(candidate: dict[str, Any]) -> float:
    metrics = candidate.get("metrics", {})
    return sum(float(metrics.get(name, 0.0)) for name in THRESHOLDS)


def passes_gate(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    metrics = candidate.get("metrics", {})
    for name, threshold in THRESHOLDS.items():
        value = float(metrics.get(name, 0.0))
        if value < threshold:
            reasons.append(f"{name}={value:.3f} below {threshold:.3f}")
    priority = candidate.get("priority_cases", {})
    severe_false_answers = [
        case_id
        for case_id, verdict in priority.items()
        if str(verdict).lower() == "severe_false_answer"
    ]
    if severe_false_answers:
        reasons.append("severe false answers: " + ", ".join(severe_false_answers))
    regressions = candidate.get("regressions", [])
    if regressions:
        reasons.append("regressions present: " + ", ".join(map(str, regressions)))
    return not reasons, reasons


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Select the best Fiorell.IA checkpoint from manually scored candidate metrics.",
    )
    parser.add_argument("--scores", required=True, type=Path, help="JSON file containing a candidates array.")
    args = parser.parse_args()

    data = load_json(args.scores)
    candidates = data.get("candidates", [])
    if not candidates:
        raise SystemExit("No candidates found.")

    ranked = sorted(candidates, key=candidate_score, reverse=True)
    best = ranked[0]
    passes, reasons = passes_gate(best)

    print(f"best_checkpoint={best.get('checkpoint')}")
    print(f"score={candidate_score(best):.3f}")
    print(f"decision={'GO_CANDIDATE' if passes else 'NO_GO'}")
    if reasons:
        print("reasons:")
        for reason in reasons:
            print(f"- {reason}")
    return 0 if passes else 1


if __name__ == "__main__":
    raise SystemExit(main())
