#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from genisia_rag_engine import MIN_SCORE_TO_ANSWER, TOP_K, SearchResult, engine  # noqa: E402
from domain_gate import evaluate_domain_gate  # noqa: E402
from config import settings  # noqa: E402


REQUIRED_ASK_KEYS = {
    "question",
    "answer",
    "model",
    "confidence",
    "sources",
    "noAnswer",
    "reason",
    "durationMs",
}


@dataclass
class EvalCase:
    id: str
    category: str
    query: str
    expected_sources: list[str]
    expected_no_answer: bool
    reference_answer: str | None = None


def load_dataset(path: Path) -> list[EvalCase]:
    cases = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            raw = json.loads(line)
            cases.append(
                EvalCase(
                    id=raw.get("id") or f"case_{line_no}",
                    category=raw.get("category", "uncategorized"),
                    query=raw["query"],
                    expected_sources=raw.get("expected_sources", []),
                    expected_no_answer=bool(raw.get("expected_no_answer", False)),
                    reference_answer=raw.get("reference_answer"),
                )
            )
    return cases


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def tokenize(text: str) -> set[str]:
    stopwords = {
        "alla", "allo", "anche", "che", "con", "dei", "del", "della", "delle", "gli", "il",
        "nel", "nella", "per", "piu", "puo", "qual", "quale", "sono", "the", "and", "for",
        "from", "that", "this", "with",
    }
    return {
        token
        for token in re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}", normalize_text(text))
        if token not in stopwords
    }


def source_matches(expected: str, source: str) -> bool:
    return normalize_text(expected) in normalize_text(source)


def source_hit(expected_sources: list[str], retrieved_sources: list[str]) -> bool:
    if not expected_sources:
        return True
    return any(source_matches(expected, source) for expected in expected_sources for source in retrieved_sources)


def missing_expected_sources(expected_sources: list[str], retrieved_sources: list[str]) -> list[str]:
    return [
        expected
        for expected in expected_sources
        if not any(source_matches(expected, source) for source in retrieved_sources)
    ]


def groundedness_score(answer: str, chunks: list[str]) -> float | None:
    answer_terms = tokenize(answer)
    context_terms = tokenize(" ".join(chunks))
    if not answer_terms:
        return None
    return len(answer_terms & context_terms) / len(answer_terms)


def schema_valid(response: dict[str, Any] | None) -> bool:
    if response is None:
        return False
    if not REQUIRED_ASK_KEYS.issubset(response.keys()):
        return False
    if response["confidence"] not in {"high", "medium", "low"}:
        return False
    if not isinstance(response["sources"], list):
        return False
    return True


def result_sources(results: list[SearchResult]) -> list[str]:
    return [item.source for item in results]


def result_chunks(results: list[SearchResult]) -> list[str]:
    return [item.chunk for item in results]


def parse_thresholds(raw: str | None) -> list[float]:
    if not raw:
        return []
    return [float(item.strip()) for item in raw.split(",") if item.strip()]


def is_domain_gate_pass(query: str) -> bool:
    try:
        decision = evaluate_domain_gate(
            query,
            enabled=True,
            mode=settings.domain_gate_mode,
            terms_path=settings.domain_gate_terms_path,
        )
        return decision.passed
    except Exception:
        # Fallback to previous lightweight heuristic if domain gate evaluation fails
        terms = tokenize(query)
        excluded_terms = {
            "antiriciclaggio", "aml", "customer", "disclosure", "disclosures", "esenzioni",
            "gdpr", "mifid", "psd2", "retail", "sfdr", "suitability",
        }
        if terms & excluded_terms:
            return False

        domain_terms = {
            "banca", "bancaria", "banche", "basel", "basilea", "capital", "capitale", "circ",
            "circolare", "credito", "creditizi", "creditizio", "crr", "default", "ecl", "eba",
            "esposizione", "esposizioni", "ifrs", "impairment", "prudenziale", "rischio",
            "regulation", "requirements", "sicr", "stage", "vigilanza",
        }
        return bool(terms & domain_terms)


def predict_no_answer(results: list[SearchResult], threshold: float, min_score_gap: float | None, use_domain_gate: bool, query: str) -> bool:
    if not results:
        return True
    if use_domain_gate and not is_domain_gate_pass(query):
        return True
    top_score = results[0].score
    second_score = results[1].score if len(results) > 1 else 0.0
    if top_score < threshold:
        return True
    if min_score_gap is not None and len(results) > 1 and (top_score - second_score) < min_score_gap:
        return True
    return False


def run_case(
    case: EvalCase,
    top_k: int,
    generate: bool,
    threshold: float = MIN_SCORE_TO_ANSWER,
    min_score_gap: float | None = None,
    use_domain_gate: bool = False,
) -> dict[str, Any]:
    started = time.perf_counter()
    error = None
    response = None
    answer = ""

    try:
        results = engine.search(case.query, top_k=top_k)
        top_score = results[0].score if results else 0.0
        second_score = results[1].score if len(results) > 1 else 0.0
        score_gap = top_score - second_score if results else 0.0
        predicted_no_answer = predict_no_answer(results, threshold, min_score_gap, use_domain_gate, case.query)

        if generate:
            response = engine.ask(case.query, top_k=top_k)
            predicted_no_answer = bool(response.get("noAnswer", False))
            answer = response.get("answer", "")

        retrieved_sources = result_sources(results)
        retrieved_chunks = result_chunks(results)
        hit = source_hit(case.expected_sources, retrieved_sources)
        missing_sources = missing_expected_sources(case.expected_sources, retrieved_sources)
        groundedness = groundedness_score(answer, retrieved_chunks) if generate and not predicted_no_answer else None
        valid_schema = schema_valid(response) if generate else True
    except Exception as exc:
        results = []
        top_score = 0.0
        second_score = 0.0
        score_gap = 0.0
        predicted_no_answer = False
        retrieved_sources = []
        hit = False
        missing_sources = case.expected_sources
        groundedness = None
        valid_schema = False
        error = str(exc)

    latency_ms = int((time.perf_counter() - started) * 1000)
    no_answer_correct = predicted_no_answer == case.expected_no_answer
    false_answer = case.expected_no_answer and not predicted_no_answer
    false_no_answer = (not case.expected_no_answer) and predicted_no_answer

    return {
        "id": case.id,
        "category": case.category,
        "query": case.query,
        "expectedSources": case.expected_sources,
        "retrievedSources": retrieved_sources,
        "topScore": top_score,
        "secondScore": second_score,
        "scoreGap": score_gap,
        "sourceHit": hit,
        "missingExpectedSources": missing_sources,
        "expectedNoAnswer": case.expected_no_answer,
        "predictedNoAnswer": predicted_no_answer,
        "noAnswerCorrect": no_answer_correct,
        "falseAnswer": false_answer,
        "falseNoAnswer": false_no_answer,
        "schemaValid": valid_schema,
        "groundedness": groundedness,
        "latencyMs": latency_ms,
        "threshold": threshold,
        "minScoreGap": min_score_gap,
        "domainGate": use_domain_gate,
        "error": error,
        "_rawResults": results,
    }


def mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def aggregate(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(case_results)
    source_expected = [item for item in case_results if item["expectedSources"]]
    in_domain = [item for item in case_results if not item["expectedNoAnswer"]]
    groundedness_values = [
        item["groundedness"]
        for item in case_results
        if isinstance(item.get("groundedness"), (int, float))
    ]
    latencies = [item["latencyMs"] for item in case_results]

    return {
        "caseCount": total,
        "sourceHitRate": sum(1 for item in source_expected if item["sourceHit"]) / len(source_expected) if source_expected else None,
        "inDomainCoverage": sum(1 for item in in_domain if not item["predictedNoAnswer"]) / len(in_domain) if in_domain else None,
        "noAnswerAccuracy": sum(1 for item in case_results if item["noAnswerCorrect"]) / total if total else None,
        "schemaValidityRate": sum(1 for item in case_results if item["schemaValid"]) / total if total else None,
        "avgLatencyMs": mean(latencies),
        "p50LatencyMs": statistics.median(latencies) if latencies else None,
        "avgGroundedness": mean(groundedness_values),
        "falseAnswerCount": sum(1 for item in case_results if item["falseAnswer"]),
        "falseNoAnswerCount": sum(1 for item in case_results if item["falseNoAnswer"]),
        "errorCount": sum(1 for item in case_results if item["error"]),
    }


def aggregate_by_category(case_results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    categories = sorted({item["category"] for item in case_results})
    return {
        category: aggregate([item for item in case_results if item["category"] == category])
        for category in categories
    }


def group_failed_by_category(case_results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in case_results:
        if item["error"] or not item["sourceHit"] or not item["noAnswerCorrect"] or not item["schemaValid"]:
            grouped.setdefault(item["category"], []).append(item)
    return dict(sorted(grouped.items()))


def write_json_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable_report = json.loads(json.dumps(report, ensure_ascii=False, default=str))
    with path.open("w", encoding="utf-8") as handle:
        json.dump(serializable_report, handle, ensure_ascii=False, indent=2)


def format_percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def write_markdown_report(path: Path, report: dict[str, Any]) -> None:
    metrics = report["metrics"]
    failed = report["failedCases"]
    calibration = report.get("calibration")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Gen.Is.IA RAG Evaluation Report",
        "",
        f"- Dataset: `{report['dataset']}`",
        f"- Generated at: `{report['generatedAt']}`",
        f"- Top-K: `{report['topK']}`",
        f"- Generation enabled: `{report['generationEnabled']}`",
        "",
        "## Aggregate Metrics",
        "",
        f"- Case count: `{metrics['caseCount']}`",
        f"- Source hit rate: `{format_percent(metrics['sourceHitRate'])}`",
        f"- In-domain coverage: `{format_percent(metrics['inDomainCoverage'])}`",
        f"- No-answer accuracy: `{format_percent(metrics['noAnswerAccuracy'])}`",
        f"- Schema validity rate: `{format_percent(metrics['schemaValidityRate'])}`",
        f"- Average latency: `{metrics['avgLatencyMs']:.0f} ms`" if metrics["avgLatencyMs"] is not None else "- Average latency: `n/a`",
        f"- P50 latency: `{metrics['p50LatencyMs']:.0f} ms`" if metrics["p50LatencyMs"] is not None else "- P50 latency: `n/a`",
        f"- Average groundedness: `{format_percent(metrics['avgGroundedness'])}`",
        f"- False answers: `{metrics['falseAnswerCount']}`",
        f"- False no-answers: `{metrics['falseNoAnswerCount']}`",
        f"- Errors: `{metrics['errorCount']}`",
        "",
    ]

    category_metrics = report.get("metricsByCategory", {})
    if category_metrics:
        lines.extend(
            [
                "## Metrics By Category",
                "",
                "| Category | Cases | Source hit | In-domain coverage | No-answer accuracy | False answers | False no-answers | Avg latency |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for category, category_metric in category_metrics.items():
            avg_latency = category_metric["avgLatencyMs"]
            latency_text = f"{avg_latency:.0f} ms" if avg_latency is not None else "n/a"
            lines.append(
                f"| `{category}` | {category_metric['caseCount']} | {format_percent(category_metric['sourceHitRate'])} | "
                f"{format_percent(category_metric['inDomainCoverage'])} | {format_percent(category_metric['noAnswerAccuracy'])} | "
                f"{category_metric['falseAnswerCount']} | {category_metric['falseNoAnswerCount']} | {latency_text} |"
            )
        lines.append("")

    if calibration:
        recommended = calibration["recommended"]
        lines.extend(
            [
                "## Threshold Calibration",
                "",
                f"- Recommended threshold: `{recommended['threshold']}`",
                f"- Recommendation reason: {recommended['reason']}",
                "",
                "| Threshold | Source hit | In-domain coverage | No-answer accuracy | False answers | False no-answers | Avg latency |",
                "|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for item in calibration["runs"]:
            m = item["metrics"]
            lines.append(
                f"| {item['threshold']:.3f} | {format_percent(m['sourceHitRate'])} | {format_percent(m['inDomainCoverage'])} | "
                f"{format_percent(m['noAnswerAccuracy'])} | {m['falseAnswerCount']} | {m['falseNoAnswerCount']} | "
                f"{m['avgLatencyMs']:.0f} ms |"
            )
        lines.append("")

    lines.extend(["## Failed Cases", ""])

    if not failed:
        lines.append("No failed cases.")
    else:
        for item in failed:
            lines.extend(
                [
                    f"### {item['id']}",
                    "",
                    f"- Category: `{item['category']}`",
                    f"- Query: {item['query']}",
                    f"- Expected no-answer: `{item['expectedNoAnswer']}`",
                    f"- Predicted no-answer: `{item['predictedNoAnswer']}`",
                    f"- Source hit: `{item['sourceHit']}`",
                    f"- Missing expected sources: `{', '.join(item['missingExpectedSources']) or 'none'}`",
                    f"- Top score: `{item['topScore']:.4f}`",
                    f"- Error: `{item['error'] or 'none'}`",
                    "",
                ]
            )

    failed_by_category = report.get("failedCasesByCategory", {})
    if failed_by_category:
        lines.extend(["## Failure Cases By Category", ""])
        for category, items in failed_by_category.items():
            lines.extend([f"### {category}", ""])
            for item in items:
                lines.append(
                    f"- `{item['id']}`: expected no-answer `{item['expectedNoAnswer']}`, "
                    f"predicted `{item['predictedNoAnswer']}`, source hit `{item['sourceHit']}`, "
                    f"top score `{item['topScore']:.4f}`"
                )
            lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(dataset_path: Path, case_results: list[dict[str, Any]], top_k: int, generate: bool) -> dict[str, Any]:
    public_results = []
    for item in case_results:
        public_item = dict(item)
        public_item.pop("_rawResults", None)
        public_results.append(public_item)
    failed = [
        item
        for item in public_results
        if item["error"] or not item["sourceHit"] or not item["noAnswerCorrect"] or not item["schemaValid"]
    ]
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset_path),
        "topK": top_k,
        "generationEnabled": generate,
        "threshold": public_results[0]["threshold"] if public_results else MIN_SCORE_TO_ANSWER,
        "minScoreGap": public_results[0]["minScoreGap"] if public_results else None,
        "domainGate": public_results[0]["domainGate"] if public_results else False,
        "metrics": aggregate(public_results),
        "metricsByCategory": aggregate_by_category(public_results),
        "failedCases": failed,
        "failedCasesByCategory": group_failed_by_category(public_results),
        "falseAnswers": [item for item in public_results if item["falseAnswer"]],
        "falseNoAnswers": [item for item in public_results if item["falseNoAnswer"]],
        "missingExpectedSources": [item for item in public_results if item["missingExpectedSources"]],
        "cases": public_results,
    }


def recommend_threshold(runs: list[dict[str, Any]], min_in_domain_coverage: float) -> dict[str, Any]:
    eligible = [
        run
        for run in runs
        if (run["metrics"]["inDomainCoverage"] or 0.0) >= min_in_domain_coverage
    ]
    candidates = eligible or runs
    ranked = sorted(
        candidates,
        key=lambda run: (
            run["metrics"]["noAnswerAccuracy"] or 0.0,
            -(run["metrics"]["falseAnswerCount"]),
            run["metrics"]["inDomainCoverage"] or 0.0,
            -(run["metrics"]["falseNoAnswerCount"]),
        ),
        reverse=True,
    )
    best = ranked[0]
    reason = (
        f"Best no-answer accuracy while keeping in-domain coverage >= {min_in_domain_coverage:.0%}."
        if eligible
        else "No threshold met the requested in-domain coverage floor; selected best available compromise."
    )
    return {
        "threshold": best["threshold"],
        "reason": reason,
        "metrics": best["metrics"],
    }


def build_calibration_report(
    dataset_path: Path,
    base_results: list[dict[str, Any]],
    thresholds: list[float],
    top_k: int,
    min_score_gap: float | None,
    use_domain_gate: bool,
    min_in_domain_coverage: float,
) -> dict[str, Any]:
    runs = []
    for threshold in thresholds:
        adjusted = []
        for item in base_results:
            updated = dict(item)
            predicted_no_answer = predict_no_answer(
                item["_rawResults"],
                threshold,
                min_score_gap,
                use_domain_gate,
                item["query"],
            )
            updated["predictedNoAnswer"] = predicted_no_answer
            updated["noAnswerCorrect"] = predicted_no_answer == item["expectedNoAnswer"]
            updated["falseAnswer"] = item["expectedNoAnswer"] and not predicted_no_answer
            updated["falseNoAnswer"] = (not item["expectedNoAnswer"]) and predicted_no_answer
            updated["threshold"] = threshold
            updated["minScoreGap"] = min_score_gap
            updated["domainGate"] = use_domain_gate
            updated.pop("_rawResults", None)
            adjusted.append(updated)

        failed = [
            item
            for item in adjusted
            if item["error"] or not item["sourceHit"] or not item["noAnswerCorrect"] or not item["schemaValid"]
        ]
        runs.append(
            {
                "threshold": threshold,
                "metrics": aggregate(adjusted),
                "metricsByCategory": aggregate_by_category(adjusted),
                "failedCases": failed,
                "falseAnswers": [item for item in adjusted if item["falseAnswer"]],
                "falseNoAnswers": [item for item in adjusted if item["falseNoAnswer"]],
            }
        )

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset_path),
        "topK": top_k,
        "generationEnabled": False,
        "minScoreGap": min_score_gap,
        "domainGate": use_domain_gate,
        "runs": runs,
        "recommended": recommend_threshold(runs, min_in_domain_coverage),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local evaluation benchmark against the existing Gen.Is.IA RAG pipeline.")
    parser.add_argument("--dataset", type=Path, default=Path(__file__).with_name("dataset.jsonl"))
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("reports") / "latest.json")
    parser.add_argument("--markdown", type=Path, default=Path(__file__).with_name("reports") / "latest.md")
    parser.add_argument("--top-k", type=int, default=TOP_K)
    parser.add_argument("--generate", action="store_true", help="Call the LLM and compute answer-level metrics. Slower, fully local.")
    parser.add_argument("--threshold", type=float, default=MIN_SCORE_TO_ANSWER, help="Score threshold for no-answer prediction in non-generation mode.")
    parser.add_argument("--calibrate-thresholds", type=str, help="Comma-separated thresholds to compare, e.g. 0.12,0.18,0.22,0.25,0.30.")
    parser.add_argument("--min-score-gap", type=float, default=None, help="Optional abstention rule: require top score minus second score to be at least this value.")
    parser.add_argument("--domain-gate", action="store_true", help="Optional abstention rule: require simple domain keywords in the query.")
    parser.add_argument("--min-in-domain-coverage", type=float, default=0.8, help="Coverage floor used to recommend a threshold.")
    args = parser.parse_args()

    cases = load_dataset(args.dataset)

    if args.calibrate_thresholds:
        thresholds = parse_thresholds(args.calibrate_thresholds)
        if not thresholds:
            raise SystemExit("No valid thresholds supplied.")
        base_results = [
            run_case(
                case,
                top_k=args.top_k,
                generate=False,
                threshold=args.threshold,
                min_score_gap=args.min_score_gap,
                use_domain_gate=args.domain_gate,
            )
            for case in cases
        ]
        calibration = build_calibration_report(
            args.dataset,
            base_results,
            thresholds,
            top_k=args.top_k,
            min_score_gap=args.min_score_gap,
            use_domain_gate=args.domain_gate,
            min_in_domain_coverage=args.min_in_domain_coverage,
        )
        recommended_threshold = calibration["recommended"]["threshold"]
        recommended_results = []
        for result in base_results:
            item = dict(result)
            predicted_no_answer = predict_no_answer(item["_rawResults"], recommended_threshold, args.min_score_gap, args.domain_gate, item["query"])
            item["predictedNoAnswer"] = predicted_no_answer
            item["noAnswerCorrect"] = predicted_no_answer == item["expectedNoAnswer"]
            item["falseAnswer"] = item["expectedNoAnswer"] and not predicted_no_answer
            item["falseNoAnswer"] = (not item["expectedNoAnswer"]) and predicted_no_answer
            item["threshold"] = recommended_threshold
            item["minScoreGap"] = args.min_score_gap
            item["domainGate"] = args.domain_gate
            recommended_results.append(item)
        report = build_report(args.dataset, recommended_results, top_k=args.top_k, generate=False)
        report["calibration"] = calibration
    else:
        results = [
            run_case(
                case,
                top_k=args.top_k,
                generate=args.generate,
                threshold=args.threshold,
                min_score_gap=args.min_score_gap,
                use_domain_gate=args.domain_gate,
            )
            for case in cases
        ]
        report = build_report(args.dataset, results, top_k=args.top_k, generate=args.generate)

    write_json_report(args.out, report)
    write_markdown_report(args.markdown, report)

    metrics = report["metrics"]
    print(f"cases={metrics['caseCount']}")
    print(f"source_hit_rate={format_percent(metrics['sourceHitRate'])}")
    print(f"no_answer_accuracy={format_percent(metrics['noAnswerAccuracy'])}")
    print(f"schema_validity_rate={format_percent(metrics['schemaValidityRate'])}")
    print(f"avg_latency_ms={metrics['avgLatencyMs']:.0f}" if metrics["avgLatencyMs"] is not None else "avg_latency_ms=n/a")
    print(f"avg_groundedness={format_percent(metrics['avgGroundedness'])}")
    print(f"false_answers={metrics['falseAnswerCount']}")
    print(f"false_no_answers={metrics['falseNoAnswerCount']}")
    if "calibration" in report:
        recommended = report["calibration"]["recommended"]
        print(f"recommended_threshold={recommended['threshold']}")
        print(f"recommendation={recommended['reason']}")
    print(f"report_json={args.out}")
    print(f"report_md={args.markdown}")

    return 1 if report["failedCases"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
