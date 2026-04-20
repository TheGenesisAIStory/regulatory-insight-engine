#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from genisia_rag_engine import (
    CACHE_FILE,
    CORPUS_MANIFEST_FILE,
    DOCS_DIR,
    INDEX_MANIFEST_FILE,
    cache_state,
    configured_pdf_paths,
    download_all,
    engine,
    save_corpus_manifest,
)


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def lifecycle_status() -> dict[str, Any]:
    pdf_paths = configured_pdf_paths(load_only_ifrs9=False)
    state = cache_state(pdf_paths)
    return {
        "docsDir": str(DOCS_DIR),
        "documents": len(pdf_paths),
        "corpusManifest": str(CORPUS_MANIFEST_FILE),
        "corpusManifestExists": CORPUS_MANIFEST_FILE.exists(),
        "cacheFile": str(CACHE_FILE),
        "indexManifest": str(INDEX_MANIFEST_FILE),
        "indexManifestExists": INDEX_MANIFEST_FILE.exists(),
        "cacheExists": state["cacheExists"],
        "cacheReadable": state["cacheReadable"],
        "cacheValid": state["cacheValid"],
        "cacheStale": state["cacheStale"],
        "cachedChunks": state["chunks"],
        "readyForFastStartup": bool(pdf_paths and state["cacheValid"]),
    }


def command_status(_: argparse.Namespace) -> int:
    print_json(lifecycle_status())
    return 0


def command_download(_: argparse.Namespace) -> int:
    download_all()
    print_json(lifecycle_status())
    return 0


def command_manifest(_: argparse.Namespace) -> int:
    save_corpus_manifest()
    print_json(lifecycle_status())
    return 0


def command_rebuild(args: argparse.Namespace) -> int:
    engine.initialize(rebuild=True, download=args.download)
    print_json(lifecycle_status() | {"chunksLoaded": len(engine.chunks)})
    return 0


def command_ready(_: argparse.Namespace) -> int:
    status = lifecycle_status()
    print_json(status)
    return 0 if status["readyForFastStartup"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local corpus lifecycle commands for the offline regulatory RAG.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Report corpus/cache/index readiness.").set_defaults(func=command_status)
    subparsers.add_parser("download", help="Download or update configured regulatory documents.").set_defaults(func=command_download)
    subparsers.add_parser("manifest", help="Refresh the local corpus manifest without downloading.").set_defaults(func=command_manifest)
    subparsers.add_parser("ready", help="Exit 0 when corpus and cache are valid for fast startup.").set_defaults(func=command_ready)

    rebuild = subparsers.add_parser("rebuild", help="Rebuild the persistent embeddings cache from the local corpus.")
    rebuild.add_argument(
        "--download",
        action="store_true",
        help="Download/update configured documents before rebuilding the index.",
    )
    rebuild.set_defaults(func=command_rebuild)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
