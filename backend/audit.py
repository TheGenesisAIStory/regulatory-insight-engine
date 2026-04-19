from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from config import settings


def configure_logging() -> logging.Logger:
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("genisia")
    logger.setLevel(settings.log_level)

    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
        file_handler = logging.FileHandler(settings.log_dir / "download_normativa.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger


logger = configure_logging()


def hash_query(query: str) -> str:
    return sha256(query.strip().encode("utf-8")).hexdigest()[:16]


def audit_query(event: dict[str, Any]) -> None:
    settings.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    with settings.audit_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
