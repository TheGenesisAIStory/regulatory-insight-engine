#!/usr/bin/env python3
from __future__ import annotations

import time

try:
    from colorama import Fore, Style, init

    init(autoreset=True)
except Exception:
    class Fore:
        CYAN = "\033[36m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        MAGENTA = "\033[35m"
        WHITE = "\033[37m"

    class Style:
        BRIGHT = "\033[1m"
        RESET_ALL = "\033[0m"


RESET = Style.RESET_ALL


def pause() -> None:
    time.sleep(0.3)


def emit(text: str = "", color: str = "") -> None:
    print(f"{color}{text}{RESET if color else ''}")


def main() -> None:
    pause()
    emit("╔══════════════════════════════════════════════════════════╗", Fore.CYAN + Style.BRIGHT)
    emit("║   Regulatory Insight Engine — v0.1.0-beta                ║", Fore.CYAN + Style.BRIGHT)
    emit("║   Offline RAG Demo — Banking Compliance                  ║", Fore.CYAN + Style.BRIGHT)
    emit("╚══════════════════════════════════════════════════════════╝", Fore.CYAN + Style.BRIGHT)
    emit()

    pause()
    emit("► Query: Quali sono i requisiti di capitale CRR per il rischio di credito?", Fore.WHITE + Style.BRIGHT)
    emit()

    pause()
    emit("⏳ Recupero contesto dal corpus locale...", Fore.YELLOW)
    emit()

    pause()
    emit("✓ 2 chunks rilevanti trovati  |  Score massimo: 0.87  |  Modello: ollama/mistral", Fore.GREEN + Style.BRIGHT)
    emit()

    pause()
    emit("┌─ Risposta ────────────────────────────────────────────────", Fore.MAGENTA + Style.BRIGHT)
    emit("│ Secondo l'art. 92 CRR, gli enti creditizi devono mantenere", Fore.MAGENTA)
    emit("│ un Common Equity Tier 1 (CET1) pari ad almeno il 4,5%", Fore.MAGENTA)
    emit("│ dell'importo totale dell'esposizione al rischio (TREA).", Fore.MAGENTA)
    emit("│ Il Tier 1 complessivo deve essere almeno il 6%, il Total", Fore.MAGENTA)
    emit("│ Capital Ratio almeno l'8%.", Fore.MAGENTA)
    emit("└───────────────────────────────────────────────────────────", Fore.MAGENTA + Style.BRIGHT)
    emit()

    pause()
    emit("📎 Fonti:", Fore.CYAN + Style.BRIGHT)
    emit("   [1] CRR — Art. 92, Requisiti di fondi propri", Fore.CYAN)
    emit("   [2] EBA Guidelines — SREP 2023, Sezione 4.2", Fore.CYAN)
    emit()

    pause()
    emit("⚡ Generato offline in 1.4s — nessuna connessione esterna", Fore.GREEN + Style.BRIGHT)
    emit("   Nessun dato inviato a server di terze parti.", Fore.GREEN)


if __name__ == "__main__":
    main()
