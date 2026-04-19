#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import pickle
import re
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import fitz
import numpy as np
import requests
from bs4 import BeautifulSoup

from audit import audit_query, hash_query, logger
from config import settings
from domain_gate import evaluate_domain_gate

warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

PROJECT_ROOT = settings.project_root
BASE_DIR = settings.base_dir
DOCS_DIR = settings.docs_path
CACHE_FILE = settings.cache_path
LOG_DIR = settings.log_dir

EMBED_MODEL = settings.embed_model
CHAT_MODEL = settings.llm_model
OLLAMA_BASE_URL = settings.ollama_host

USE_PROXY = settings.use_proxy
PROXIES = {
    "http": settings.http_proxy,
    "https": settings.https_proxy,
}

DEFAULT_INDEX_CATEGORIES = "ifrs9,crr,banca_ditalia"
INDEX_CATEGORIES = settings.index_categories
CRAWL_PDF_PAGES = settings.crawl_pdf_pages
TOP_K = settings.top_k
CHUNK_WORDS = settings.chunk_size
CHUNK_OVERLAP = settings.chunk_overlap
BATCH_SIZE = settings.batch_size
MAX_EMBED_CHARS = settings.max_embed_chars
MIN_SCORE_TO_ANSWER = settings.score_threshold

QUERY_EXPANSIONS = {
    "sicr": "significant increase in credit risk credit risk has increased significantly stage 2 lifetime expected credit losses 30 days past due rebuttable presumption",
    "soglia": "threshold thresholds more than 30 days past due significant increase low credit risk default probability",
    "soglie": "threshold thresholds more than 30 days past due significant increase low credit risk default probability",
    "pd": "probability of default probability that a counterparty defaults one-year period risk of default occurring",
    "default": "default probability of default past due credit-impaired",
    "default?": "probability of default probability that a counterparty defaults one-year period",
    "inadempienza": "default probability of default past due credit-impaired",
    "probabilità": "probability probability of default expected credit losses",
    "probabilita": "probability probability of default expected credit losses",
    "aumento": "significant increase in credit risk credit risk has increased significantly",
    "significativo": "significant increase in credit risk credit risk has increased significantly",
    "rischio": "credit risk risk of default occurring",
    "credito": "credit risk financial instrument borrower counterparty",
    "stadio": "stage stage 1 stage 2 stage 3 lifetime expected credit losses 12-month expected credit losses",
    "fase": "stage stage 1 stage 2 stage 3 lifetime expected credit losses 12-month expected credit losses",
    "perdita": "expected credit losses lifetime expected credit losses loss allowance",
    "perdite": "expected credit losses lifetime expected credit losses loss allowance",
    "attese": "expected credit losses lifetime expected credit losses loss allowance",
    "scaduto": "past due more than 30 days past due rebuttable presumption",
    "scaduti": "past due more than 30 days past due rebuttable presumption",
    "ecl": "expected credit losses lifetime expected credit losses 12-month expected credit losses loss allowance",
}

STOPWORDS = {
    "and", "are", "for", "from", "has", "how", "the", "una", "uno", "what", "when", "where",
    "which", "with", "come", "cosa", "sono", "qual", "quali",
}

IMPORTANT_PHRASES = (
    "significant increase in credit risk",
    "credit risk has increased significantly",
    "more than 30 days past due",
    "probability of default",
    "one-year period",
    "expected credit losses",
    "lifetime expected credit losses",
    "low credit risk",
)

RESOURCES = {
    "ifrs9": [
        (
            "IFRS9",
            "https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2021/issued/part-a/ifrs-9-financial-instruments.pdf",
        )
    ],
    "crr": [
        (
            "CRR",
            "https://www.true-sale-international.de/fileadmin/tsi-gmbh/downloads/Regelwerke_und_Gesetzestexte/22a_CRR_english.pdf",
        )
    ],
    "basel": [
        ("Basel_Framework", "https://www.bis.org/baselframework/BaselFramework.pdf"),
        ("Basel_III_Post_Crisis", "https://www.bis.org/bcbs/publ/d424.pdf"),
    ],
    "banca_ditalia": [
        (
            "Circ_285_Atto_emanazione_28_agg",
            "https://www.bancaditalia.it/compiti/vigilanza/normativa/archivio-norme/circolari/c285/Atto_di_emanazione_28_aggto_285.pdf",
        ),
    ],
}

SESSION = requests.Session()
SESSION.trust_env = not USE_PROXY
if USE_PROXY:
    SESSION.proxies.update(PROXIES)


@dataclass
class SearchResult:
    chunk: str
    source: str
    score: float
    dense_score: float
    keyword_score: float


class RagError(RuntimeError):
    status_code = 500


class OllamaUnavailableError(RagError):
    status_code = 503


class RagInitializationError(RagError):
    status_code = 503


def safe_get_json(response: requests.Response) -> dict[str, Any]:
    try:
        response.raise_for_status()
    except Exception as exc:
        detail = response.text[:500] if response.text else str(exc)
        raise RuntimeError(f"Errore HTTP da Ollama: {detail}") from exc

    try:
        return response.json()
    except Exception as exc:
        raise RuntimeError(f"Risposta non valida dal server: {exc}") from exc


def check_ollama_running() -> None:
    try:
        response = SESSION.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        response.raise_for_status()
    except Exception as exc:
        raise OllamaUnavailableError(
            f"Ollama non risponde su {OLLAMA_BASE_URL}. Avvia prima 'ollama serve' in un altro terminale."
        ) from exc


def list_ollama_models() -> list[str]:
    response = SESSION.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
    data = safe_get_json(response)
    return [item.get("name") or item.get("model") for item in data.get("models", []) if item.get("name") or item.get("model")]


def resolve_chat_model(preferred: str | None = None) -> str:
    available = list_ollama_models()
    wanted = preferred or CHAT_MODEL

    if wanted in available:
        return wanted

    if ":" not in wanted and f"{wanted}:latest" in available:
        return f"{wanted}:latest"

    base_name = wanted.split(":", 1)[0]
    for model in available:
        if model.split(":", 1)[0] == base_name:
            return model

    chat_candidates = [model for model in available if "embed" not in model.lower() and "embedding" not in model.lower()]
    if chat_candidates:
        return chat_candidates[0]

    raise RuntimeError(
        f"Nessun modello chat disponibile in Ollama. Richiesto '{wanted}'. "
        f"Installa un modello con 'ollama pull {wanted}' oppure imposta GENISIA_CHAT_MODEL."
    )


def ensure_directories() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    return vec if norm == 0 else vec / norm


def get_extension_from_url(url: str) -> str:
    path = urlparse(url).path
    ext = os.path.splitext(path)[1]
    return ext if ext else ".pdf"


def download_file(url: str, path: Path, timeout: int = 60) -> None:
    if path.exists():
        logger.info("File gia' presente: %s", path.name)
        return

    logger.info("Scarico %s -> %s", url, path)
    response = SESSION.get(url, stream=True, timeout=timeout)
    response.raise_for_status()

    with path.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                handle.write(chunk)


def find_pdf_links(page_url: str, timeout: int = 60) -> list[str]:
    try:
        response = SESSION.get(page_url, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        pdf_urls = [urljoin(page_url, link["href"]) for link in soup.select("a[href]") if ".pdf" in link["href"].lower()]

        seen = set()
        deduped = []
        for url in pdf_urls:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
        return deduped
    except Exception as exc:
        logger.error("Errore analizzando %s: %s", page_url, exc)
        return []


def download_pdfs_from_page(category: str, page_url: str) -> None:
    folder = DOCS_DIR / category
    folder.mkdir(parents=True, exist_ok=True)

    for index, pdf_url in enumerate(find_pdf_links(page_url), start=1):
        base_name = os.path.basename(urlparse(pdf_url).path) or f"doc_{index}.pdf"
        try:
            download_file(pdf_url, folder / base_name)
        except Exception as exc:
            logger.error("Errore scaricando %s: %s", pdf_url, exc)


def download_all() -> None:
    ensure_directories()

    for category, items in RESOURCES.items():
        folder = DOCS_DIR / category
        folder.mkdir(parents=True, exist_ok=True)

        for name, url in items:
            try:
                ext = get_extension_from_url(url)
                if ext.lower() == ".pdf":
                    download_file(url, folder / f"{name}.pdf")
                elif CRAWL_PDF_PAGES:
                    download_pdfs_from_page(category, url)
            except Exception as exc:
                logger.error("Errore download %s: %s", url, exc)


def configured_pdf_paths(load_only_ifrs9: bool = False) -> list[Path]:
    categories = ("ifrs9",) if load_only_ifrs9 else INDEX_CATEGORIES
    paths: list[Path] = []

    for category in categories:
        folder = DOCS_DIR / category
        configured_names = [name for name, _ in RESOURCES.get(category, [])]
        configured_paths = [folder / f"{name}.pdf" for name in configured_names]
        existing_configured_paths = [path for path in configured_paths if path.exists()]
        paths.extend(existing_configured_paths or folder.glob("*.pdf"))

    return sorted(paths)


def load_pdf_pages(file_path: Path) -> list[tuple[int, str]]:
    doc = fitz.open(file_path)
    pages = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        if text and text.strip():
            pages.append((page_num, text))
    return pages


def load_all_docs(load_only_ifrs9: bool = False) -> list[tuple[str, list[tuple[int, str]]]]:
    docs = []
    for pdf in configured_pdf_paths(load_only_ifrs9=load_only_ifrs9):
        try:
            pages = load_pdf_pages(pdf)
            if pages:
                docs.append((pdf.name, pages))
        except Exception as exc:
            logger.error("Errore lettura %s: %s", pdf.name, exc)
    return docs


def chunk_text(text: str, size: int = CHUNK_WORDS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks = []
    step = max(1, size - overlap)
    for start in range(0, len(words), step):
        chunk_words = words[start:start + size]
        chunks.append(" ".join(chunk_words))
        if start + size >= len(words):
            break
    return chunks


def expand_query(query: str) -> str:
    normalized = re.findall(r"\w+", query.lower())
    expansions = [QUERY_EXPANSIONS[token] for token in normalized if token in QUERY_EXPANSIONS]
    return " ".join([query, *expansions])


def embedding_input(text: str) -> str:
    clean = " ".join(text.split())
    return clean[:MAX_EMBED_CHARS]


def embed_batch(batch: list[str]) -> list[np.ndarray]:
    response = SESSION.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": [embedding_input(text) for text in batch]},
        timeout=settings.request_timeout_seconds,
    )
    data = safe_get_json(response)
    if "embeddings" not in data:
        raise RuntimeError("La risposta embeddings di Ollama non contiene il campo 'embeddings'.")
    return [normalize(np.array(v, dtype=np.float32)) for v in data["embeddings"]]


def embed(texts: list[str]) -> list[np.ndarray]:
    if not texts:
        return []

    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        try:
            batch_embeddings = embed_batch(batch)
        except Exception:
            if len(batch) == 1:
                raise
            batch_embeddings = []
            for text in batch:
                batch_embeddings.extend(embed_batch([text]))
        all_embeddings.extend(batch_embeddings)
    return all_embeddings


def document_fingerprint(pdf_paths: list[Path]) -> list[tuple[str, int, int]]:
    fingerprint = []
    for pdf in sorted(pdf_paths):
        stat = pdf.stat()
        try:
            relative_path = str(pdf.relative_to(BASE_DIR))
        except ValueError:
            relative_path = str(pdf)
        fingerprint.append((relative_path, stat.st_size, int(stat.st_mtime)))
    return fingerprint


def cache_metadata(pdf_paths: list[Path]) -> str:
    raw = repr(
        {
            "embed_model": EMBED_MODEL,
            "max_embed_chars": MAX_EMBED_CHARS,
            "chunk_words": CHUNK_WORDS,
            "chunk_overlap": CHUNK_OVERLAP,
            "docs": document_fingerprint(pdf_paths),
        }
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_embeddings_cache(pdf_paths: list[Path]):
    if not CACHE_FILE.exists():
        return None

    try:
        with CACHE_FILE.open("rb") as handle:
            cached = pickle.load(handle)
    except Exception:
        return None

    if cached.get("metadata") != cache_metadata(pdf_paths):
        return None

    return cached["chunks"], cached["sources"], cached["embeddings"]


def save_embeddings_cache(chunks, sources, embeddings, pdf_paths: list[Path]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": cache_metadata(pdf_paths),
        "chunks": chunks,
        "sources": sources,
        "embeddings": embeddings,
    }
    with CACHE_FILE.open("wb") as handle:
        pickle.dump(payload, handle)


def keyword_score(query: str, chunk: str) -> float:
    expanded = expand_query(query).lower()
    query_terms = {
        term for term in re.findall(r"\w{3,}", expanded)
        if term not in STOPWORDS
    }
    if not query_terms:
        return 0.0

    chunk_lower = chunk.lower()
    chunk_terms = set(re.findall(r"\w{3,}", chunk_lower))
    overlap = query_terms & chunk_terms
    term_score = len(overlap) / max(6, len(query_terms))
    phrase_score = sum(0.08 for phrase in IMPORTANT_PHRASES if phrase in expanded and phrase in chunk_lower)
    definition_score = 0.0
    if (
        "probability of default" in expanded
        and "probability of default" in chunk_lower
        and "means" in chunk_lower
        and "one-year period" in chunk_lower
    ):
        definition_score = 0.25

    return min(1.0, term_score + phrase_score + definition_score)


def parse_source(source: str) -> tuple[str, int]:
    match = re.match(r"(.+)\s+p\.\s+(\d+)$", source)
    if not match:
        return source, 0
    return match.group(1), int(match.group(2))


def confidence_from_score(score: float) -> str:
    if score >= 0.35:
        return "high"
    if score >= MIN_SCORE_TO_ANSWER:
        return "medium"
    return "low"


def no_answer_message() -> str:
    return (
        "Non ho trovato un contesto abbastanza affidabile nei documenti indicizzati. "
        "Prova con una domanda piu' specifica o verifica che la normativa corretta sia presente."
    )


class GenisiaEngine:
    def __init__(self) -> None:
        self.chunks: list[str] = []
        self.sources: list[str] = []
        self.embeddings: list[np.ndarray] = []
        self.ready = False
        self.last_error: str | None = None

    def initialize(self, rebuild: bool = False, download: bool = True) -> None:
        self.last_error = None
        check_ollama_running()
        if download:
            download_all()

        docs = load_all_docs(load_only_ifrs9=False)
        if not docs:
            raise RagInitializationError(f"Nessun documento caricato da {DOCS_DIR}.")

        pdf_paths = configured_pdf_paths(load_only_ifrs9=False)
        cached = None if rebuild else load_embeddings_cache(pdf_paths)

        if cached:
            self.chunks, self.sources, self.embeddings = cached
        else:
            chunks = []
            sources = []
            for name, pages in docs:
                for page_num, text in pages:
                    for chunk in chunk_text(text):
                        chunks.append(chunk)
                        sources.append(f"{name} p. {page_num}")

            embeddings = embed(chunks)
            save_embeddings_cache(chunks, sources, embeddings, pdf_paths)
            self.chunks, self.sources, self.embeddings = chunks, sources, embeddings

        self.ready = True
        logger.info("Indice pronto: docs=%s chunks=%s cache=%s", len(docs), len(self.chunks), CACHE_FILE)

    def ensure_ready(self) -> None:
        if not self.ready:
            self.initialize(download=True)

    def status(self) -> dict[str, Any]:
        pdf_paths = configured_pdf_paths(load_only_ifrs9=False)
        ollama_online = True
        error = self.last_error
        available_models: list[str] = []
        active_chat_model = None
        try:
            check_ollama_running()
            available_models = list_ollama_models()
            active_chat_model = resolve_chat_model(CHAT_MODEL)
        except Exception as exc:
            ollama_online = False
            error = str(exc)

        return {
            "ready": self.ready,
            "ollamaOnline": ollama_online,
            "baseDir": str(BASE_DIR),
            "docsDir": str(DOCS_DIR),
            "cacheFile": str(CACHE_FILE),
            "cacheExists": CACHE_FILE.exists(),
            "documents": len(pdf_paths),
            "chunks": len(self.chunks),
            "embedModel": EMBED_MODEL,
            "chatModel": CHAT_MODEL,
            "activeChatModel": active_chat_model,
            "availableModels": available_models,
            "categories": list(INDEX_CATEGORIES),
            "domainGate": {
                "enabled": settings.enable_domain_gate,
                "mode": settings.domain_gate_mode,
                "termsPath": str(settings.domain_gate_terms_path) if settings.domain_gate_terms_path else None,
            },
            "error": error,
        }

    def readiness(self) -> dict[str, Any]:
        status = self.status()
        available = status.get("availableModels", [])
        checks = {
            "ollama": bool(status["ollamaOnline"]),
            "documents": status["documents"] > 0,
            "cache": bool(status["cacheExists"]),
            "index": self.ready and status["chunks"] > 0,
            "chatModel": bool(status.get("activeChatModel")),
            "embedModel": EMBED_MODEL in available or f"{EMBED_MODEL}:latest" in available,
        }
        reasons = []
        if not checks["ollama"]:
            reasons.append("Ollama non e' raggiungibile.")
        if not checks["documents"]:
            reasons.append(f"Nessun PDF trovato in {DOCS_DIR}.")
        if not checks["index"]:
            reasons.append("Indice non ancora caricato: verra' inizializzato alla prima richiesta o tramite rebuild.")
        if not checks["chatModel"]:
            reasons.append(f"Modello chat non disponibile: {CHAT_MODEL}.")
        if not checks["embedModel"]:
            reasons.append(f"Modello embedding non disponibile: {EMBED_MODEL}.")

        return {
            "ready": all(checks.values()),
            "checks": checks,
            "status": status,
            "reasons": reasons,
        }

    def documents(self) -> list[dict[str, Any]]:
        docs = []
        for path in configured_pdf_paths(load_only_ifrs9=False):
            stat = path.stat()
            docs.append(
                {
                    "id": path.stem,
                    "title": path.stem.replace("_", " "),
                    "source": path.parent.name,
                    "pages": 0,
                    "chunks": sum(1 for src in self.sources if src.startswith(f"{path.name} p.")),
                    "status": "indexed" if self.ready else "pending",
                    "updated": stat.st_mtime,
                    "filename": path.name,
                }
            )
        return docs

    def search(self, query: str, top_k: int = TOP_K) -> list[SearchResult]:
        self.ensure_ready()
        expanded_query = expand_query(query)
        q_emb = embed([expanded_query])[0]
        dense_scores = [float(np.dot(q_emb, e)) for e in self.embeddings]
        keyword_scores = [keyword_score(query, chunk) for chunk in self.chunks]
        combined_scores = [
            (0.82 * dense) + (0.18 * keyword)
            for dense, keyword in zip(dense_scores, keyword_scores)
        ]

        idx = np.argsort(combined_scores)[-top_k:][::-1]
        return [
            SearchResult(self.chunks[i], self.sources[i], combined_scores[i], dense_scores[i], keyword_scores[i])
            for i in idx
        ]

    def ask_llm(self, question: str, context: str, model: str | None = None) -> tuple[str, str]:
        resolved_model = resolve_chat_model(model or CHAT_MODEL)
        prompt = f"""
You are Gen.Is.IA, a banking regulation assistant created by Stefano, Risk Analyst at Intesa Sanpaolo.
You specialize in IFRS 9, CRR, Basel and banking risk methodology.
Most user questions are in Italian, while many source documents are in English. Translate the retrieved English context into clear technical Italian when the question is Italian.

Domain glossary:
- SICR means Significant Increase in Credit Risk, in Italian "aumento significativo del rischio di credito".
- ECL means Expected Credit Loss, in Italian "perdita attesa su crediti".
- PD means Probability of Default, in Italian "probabilita' di default".

Context:
{context}

Question:
{question}

Rules:
- Answer in the same language as the question when possible.
- Answer only from the retrieved context above.
- Be precise, technical and concise.
- If the retrieved context is not enough, reply exactly that the indexed documents do not contain enough information.
- Mention source filename and page when possible.
- Do not invent rules, articles or paragraphs.
- Do not use external knowledge, training memory, assumptions or unstated definitions except the glossary above.
"""

        response = SESSION.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": resolved_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=settings.chat_timeout_seconds,
        )
        data = safe_get_json(response)
        content = data.get("message", {}).get("content")
        if not content:
            raise RuntimeError("La risposta chat di Ollama non contiene 'message.content'.")
        return content, resolved_model

    def ask(self, question: str, top_k: int = TOP_K, model: str | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        self.last_error = None
        results = self.search(question, top_k=top_k)
        context = "\n\n".join(
            [
                f"[Fonte: {item.source} | Score: {item.score:.3f} | Dense: {item.dense_score:.3f} | Keyword: {item.keyword_score:.3f}]\n{item.chunk}"
                for item in results
            ]
        )

        top_score = results[0].score if results else 0.0
        domain_gate = evaluate_domain_gate(
            question,
            enabled=settings.enable_domain_gate,
            mode=settings.domain_gate_mode,
            terms_path=settings.domain_gate_terms_path,
        )
        no_answer = not results or top_score < MIN_SCORE_TO_ANSWER or not domain_gate.passed
        reason = None
        if no_answer:
            answer = no_answer_message()
            reason = domain_gate.reason if not domain_gate.passed else "retrieval_score_below_threshold"
            resolved_model = model or CHAT_MODEL
        else:
            answer, resolved_model = self.ask_llm(question, context, model=model)

        sources = []
        for item in results:
            document, page = parse_source(item.source)
            sources.append(
                {
                    "id": hashlib.sha1(f"{item.source}:{item.score}".encode("utf-8")).hexdigest()[:10],
                    "document": document,
                    "reference": item.source,
                    "page": page,
                    "score": item.score,
                    "denseScore": item.dense_score,
                    "keywordScore": item.keyword_score,
                    "excerpt": item.chunk[:900],
                }
            )

        duration_ms = int((time.perf_counter() - started) * 1000)
        audit_query(
            {
                "event": "ask",
                "queryHash": hash_query(question),
                "queryLength": len(question),
                "topK": top_k,
                "model": resolved_model,
                "noAnswer": no_answer,
                "reason": reason,
                "domainGate": {
                    "enabled": settings.enable_domain_gate,
                    "mode": domain_gate.mode,
                    "passed": domain_gate.passed,
                    "matchedAllowTerms": list(domain_gate.matched_allow_terms),
                    "matchedDenyTerms": list(domain_gate.matched_deny_terms),
                },
                "durationMs": duration_ms,
                "sources": [
                    {
                        "reference": source["reference"],
                        "score": round(source["score"], 4),
                        "denseScore": round(source["denseScore"], 4),
                        "keywordScore": round(source["keywordScore"], 4),
                    }
                    for source in sources
                ],
            }
        )
        logger.info(
            "query answered hash=%s no_answer=%s top_score=%.4f sources=%s duration_ms=%s",
            hash_query(question),
            no_answer,
            top_score,
            len(sources),
            duration_ms,
        )

        return {
            "question": question,
            "answer": answer,
            "model": resolved_model,
            "confidence": "low" if no_answer else confidence_from_score(top_score),
            "sources": sources,
            "noAnswer": no_answer,
            "reason": reason,
            "durationMs": duration_ms,
        }


engine = GenisiaEngine()
