from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env(name: str, legacy_name: str | None = None, default: str | None = None) -> str:
    if name in os.environ:
        return os.environ[name]
    if legacy_name and legacy_name in os.environ:
        return os.environ[legacy_name]
    if default is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return default


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    project_root: Path
    base_dir: Path
    docs_path: Path
    cache_path: Path
    log_dir: Path
    audit_log_path: Path
    ollama_host: str
    llm_model: str
    embed_model: str
    index_categories: tuple[str, ...]
    crawl_pdf_pages: bool
    top_k: int
    chunk_size: int
    chunk_overlap: int
    batch_size: int
    max_embed_chars: int
    score_threshold: float
    enable_domain_gate: bool
    domain_gate_mode: str
    domain_gate_terms_path: Path | None
    request_timeout_seconds: int
    chat_timeout_seconds: int
    log_level: str
    use_proxy: bool
    http_proxy: str
    https_proxy: str


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[1]
    original_rag_dir = Path.home() / "GitHub" / "rag-banca"
    base_dir = Path(_env("RAG_BASE_DIR", "GENISIA_RAG_BASE_DIR", str(original_rag_dir if original_rag_dir.exists() else project_root / "rag-banca")))
    docs_path = Path(_env("DOCS_PATH", "GENISIA_DOCS_DIR", str(base_dir / "normativa")))
    cache_path = Path(_env("CACHE_PATH", "GENISIA_CACHE_FILE", str(base_dir / "genisia_embeddings_cache.pkl")))
    log_dir = Path(_env("LOG_DIR", None, str(docs_path / "log")))

    categories = tuple(
        category.strip()
        for category in _env("INDEX_CATEGORIES", "GENISIA_INDEX_CATEGORIES", "ifrs9,crr,banca_ditalia").split(",")
        if category.strip()
    )

    return Settings(
        project_root=project_root,
        base_dir=base_dir,
        docs_path=docs_path,
        cache_path=cache_path,
        log_dir=log_dir,
        audit_log_path=Path(_env("AUDIT_LOG_PATH", None, str(log_dir / "queries.jsonl"))),
        ollama_host=_env("OLLAMA_HOST", "GENISIA_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        llm_model=_env("LLM_MODEL", "GENISIA_CHAT_MODEL", "qwen2.5:3b"),
        embed_model=_env("EMBED_MODEL", "GENISIA_EMBED_MODEL", "embeddinggemma"),
        index_categories=categories,
        crawl_pdf_pages=_bool(_env("CRAWL_PDF_PAGES", "GENISIA_CRAWL_PDF_PAGES", "false")),
        top_k=int(_env("TOP_K", "GENISIA_TOP_K", "6")),
        chunk_size=int(_env("CHUNK_SIZE", "GENISIA_CHUNK_WORDS", "420")),
        chunk_overlap=int(_env("CHUNK_OVERLAP", "GENISIA_CHUNK_OVERLAP", "80")),
        batch_size=int(_env("BATCH_SIZE", "GENISIA_BATCH_SIZE", "20")),
        max_embed_chars=int(_env("MAX_EMBED_CHARS", "GENISIA_MAX_EMBED_CHARS", "1800")),
        score_threshold=float(_env("SCORE_THRESHOLD", "GENISIA_MIN_SCORE_TO_ANSWER", "0.12")),
        enable_domain_gate=_bool(_env("ENABLE_DOMAIN_GATE", None, "false")),
        domain_gate_mode=_env("DOMAIN_GATE_MODE", None, "hybrid").lower(),
        domain_gate_terms_path=Path(path) if (path := _env("DOMAIN_GATE_TERMS_PATH", None, "")) else None,
        request_timeout_seconds=int(_env("REQUEST_TIMEOUT_SECONDS", None, "120")),
        chat_timeout_seconds=int(_env("CHAT_TIMEOUT_SECONDS", None, "240")),
        log_level=_env("LOG_LEVEL", None, "INFO").upper(),
        use_proxy=_bool(_env("USE_PROXY", "GENISIA_USE_PROXY", "false")),
        http_proxy=_env("HTTP_PROXY_URL", "GENISIA_HTTP_PROXY", "http://proxy.miaazienda.it:8080"),
        https_proxy=_env("HTTPS_PROXY_URL", "GENISIA_HTTPS_PROXY", "http://proxy.miaazienda.it:8080"),
    )


settings = load_settings()
