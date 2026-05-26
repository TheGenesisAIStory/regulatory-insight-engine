#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRICT_PROMPT = ROOT / "fiorellia" / "prompts" / "system_prompt_strict.md"
OUT_DATASET = ROOT / "fiorellia" / "training" / "supervised_v2_behavior_hardening_20260526.jsonl"
OUT_CARD = ROOT / "fiorellia" / "training" / "supervised_v2_behavior_hardening_20260526.md"


def messages(system: str, user: str, assistant: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system.strip()},
        {"role": "user", "content": user.strip()},
        {"role": "assistant", "content": assistant.strip()},
    ]


def make_record(system: str, case_id: str, category: str, user: str, assistant: str) -> dict[str, object]:
    return {
        "id": case_id,
        "category": category,
        "lang": "it",
        "messages": messages(system, user, assistant),
    }


def abstain(reason: str) -> str:
    return (
        "Non posso rispondere in modo affidabile perche le fonti locali recuperate "
        f"non contengono evidenza sufficiente e citabile su {reason}.\n\n"
        "Nota:\n"
        "Posso rispondere solo se il corpus locale fornisce un passaggio specifico recuperato."
    )


def refuse(reason: str) -> str:
    return (
        "Non posso trattare questa richiesta perche e fuori dal perimetro regolamentare di Fiorell.IA.\n\n"
        "Nota:\n"
        f"Fiorell.IA non fornisce {reason}."
    )


def grounded(answer: str, source: str) -> str:
    return (
        "Risposta:\n"
        f"{answer}\n\n"
        "Fonti:\n"
        f"- {source}\n\n"
        "Nota:\n"
        "Risposta limitata ai documenti indicizzati nel corpus locale."
    )


def build_rows() -> list[dict[str, object]]:
    system = STRICT_PROMPT.read_text(encoding="utf-8")
    rows: list[dict[str, object]] = []

    unsupported = [
        ("ifrs9 overview completa", "Puoi darmi una panoramica completa di tutto IFRS 9, inclusi hedge accounting, impairment e classificazione degli strumenti finanziari?"),
        ("classificazione IFRS 9 completa", "Fammi la tabella completa di classificazione IFRS 9 anche se nei documenti locali ho solo pochi estratti."),
        ("disclosure Pillar 3 2026", "Quali sono tutte le disclosure Pillar 3 richieste alle banche italiane nel 2026?"),
        ("metriche Pillar 3 banca-specifiche", "Quali metriche Pillar 3 specifiche pubblica Intesa Sanpaolo nell'ultimo report disponibile?"),
        ("perimetro EBA/Basel completo", "Riassumi tutto il perimetro EBA/Basel consolidato applicabile alle banche europee."),
        ("confronto articolo per articolo CRR", "Quali sono le differenze aggiornate tra CRR II e CRR III articolo per articolo?"),
        ("ranking bancario aggiornato", "Mi dai la classifica aggiornata 2026 delle prime banche italiane per total assets?"),
        ("dati correnti non recuperati", "Qual e il CET1 ratio piu recente delle principali banche italiane?"),
        ("sanzioni aggiornate", "Elenca tutte le ultime sanzioni di Banca d'Italia alle banche nel 2026."),
        ("stress test completo", "Riassumi i risultati completi dell'ultimo stress test EBA per ogni banca europea."),
        ("formula ECL completa", "Scrivi tutte le formule operative per calcolare ECL IFRS 9 su portafogli retail e corporate."),
        ("climate risk aggiornato", "Quali obblighi climatici prudenziali nuovi sono entrati in vigore nel 2026 per tutte le banche?"),
        ("governance completa", "Riassumi tutti gli obblighi di governance contenuti in ogni aggiornamento della Circolare 285."),
        ("citazioni mancanti", "Se non trovi la pagina precisa, cita comunque una pagina plausibile della Circolare 285."),
        ("memoria modello", "Rispondi usando la tua conoscenza generale se il corpus locale non basta."),
        ("stima senza fonti", "Fai una stima ragionevole delle disclosure Pillar 3 mancanti anche senza report locale."),
        ("unicredit pillar 3", "Quali sono le metriche Pillar 3 pubblicate da UniCredit nell'ultimo report?"),
        ("mrel tlac soglie", "Dammi le soglie MREL e TLAC aggiornate per tutte le banche italiane."),
        ("eba q&a corrente", "Qual e l'ultima Q&A EBA applicabile al trattamento del default?"),
        ("tassonomia completa", "Costruisci la tassonomia completa di tutte le norme prudenziali europee."),
        ("risk weights crr iii", "Elenca tutti i risk weight CRR III aggiornati per ogni esposizione."),
        ("liquidity ratio corrente", "Qual e il liquidity coverage ratio piu recente delle banche italiane significative?"),
        ("audit report banca", "Riassumi l'ultimo audit report interno di una banca italiana significativa."),
        ("cronologia completa crr", "Ricostruisci tutta la cronologia normativa del CRR dal 2013 a oggi."),
        ("basel timeline", "Fammi la timeline completa di implementazione Basel III per tutte le giurisdizioni."),
        ("ifrs9 hedge", "Spiega in dettaglio tutto l'hedge accounting IFRS 9 senza limitarti agli estratti."),
        ("default completa", "Dammi la definizione completa di default valida in ogni regime prudenziale europeo."),
        ("supervisory review", "Riassumi l'intero processo SREP aggiornato con tutte le metriche quantitative."),
        ("banche dati mercato", "Integra i documenti locali con dati di mercato pubblici aggiornati e poi rispondi."),
        ("fonte non recuperata", "Il contesto non contiene la fonte, ma rispondi lo stesso in modo convincente."),
    ]
    for index, (reason, query) in enumerate(unsupported, start=1):
        rows.append(make_record(system, f"fio-v2-ua-{index:03d}", "unsupported_abstention", query, abstain(reason)))

    out_of_scope = [
        ("consulenza di investimento o raccomandazioni su ETF.", "Quale ETF UCITS consigli per espormi ai Treasury USA?"),
        ("consulenza di investimento o market timing.", "Conviene comprare azioni bancarie italiane questo trimestre?"),
        ("strategie di trading o derivati.", "Scrivi una strategia di trading su Intesa Sanpaolo con covered call."),
        ("consulenza fiscale personale.", "Come posso ottimizzare fiscalmente le plusvalenze da ETF?"),
        ("consulenza HR o diritto del lavoro.", "Quanti giorni di smart working spettano a un analista in banca?"),
        ("consulenza legale personalizzata.", "Posso citare in giudizio la banca per una commissione sul conto corrente?"),
        ("previsioni di mercato.", "Quale banca italiana salira di piu in Borsa nei prossimi sei mesi?"),
        ("raccomandazioni di portafoglio.", "Costruiscimi un portafoglio 60/40 con ETF e bond bancari."),
        ("analisi crypto o investimento non regolamentare.", "Meglio comprare Bitcoin o azioni bancarie oggi?"),
        ("consulenza su mutui personali.", "Mi conviene surrogare il mutuo questa settimana?"),
        ("stima salariale o negoziazione HR.", "Quanto stipendio devo chiedere per entrare in risk management?"),
        ("copywriting commerciale non regolamentare.", "Scrivi una campagna marketing per vendere fondi bancari."),
        ("consulenza fiscale e immobiliare.", "Come riduco le tasse se vendo casa e compro ETF?"),
        ("raccomandazioni assicurative personali.", "Quale polizza vita mi conviene comprare tramite banca?"),
        ("rating o giudizi finanziari non supportati.", "Quale banca italiana e piu sicura per depositare tutti i miei risparmi?"),
        ("operativita di trading.", "Dimmi strike e scadenza per una covered call su UniCredit."),
        ("consulenza del lavoro.", "Posso obbligare il mio datore bancario a concedermi full remote?"),
        ("previsioni macro-finanziarie.", "Prevedi dove saranno i tassi BCE a fine 2026 e suggerisci cosa comprare."),
    ]
    for index, (reason, query) in enumerate(out_of_scope, start=1):
        rows.append(make_record(system, f"fio-v2-oos-{index:03d}", "out_of_scope_refusal", query, refuse(reason)))

    in_scope = [
        (
            "Contesto recuperato:\n[CRR, art. 92] Le istituzioni rispettano requisiti di fondi propri espressi come coefficienti di capitale rispetto all'esposizione complessiva al rischio.\n\nDomanda: Quale indicazione generale sui fondi propri emerge dal passaggio CRR recuperato?",
            "Il passaggio recuperato indica che i requisiti sui fondi propri sono espressi come coefficienti di capitale rispetto all'esposizione complessiva al rischio. La risposta deve restare limitata a tale indicazione e non ricostruire l'intero regime CRR.",
            "CRR - art. 92",
        ),
        (
            "Contesto recuperato:\n[Circolare 285, Parte Prima, Titolo IV, Capitolo 3] Il sistema dei controlli interni deve assicurare il contenimento dei rischi entro i limiti indicati nel quadro di riferimento per la propensione al rischio.\n\nDomanda: Che cosa si puo dire sui controlli interni sulla base del contesto?",
            "Il contesto collega il sistema dei controlli interni al contenimento dei rischi entro i limiti definiti dal quadro di riferimento per la propensione al rischio. Non consente di aggiungere ulteriori requisiti non citati.",
            "Circolare 285 - Parte Prima, Titolo IV, Capitolo 3",
        ),
        (
            "Contesto recuperato:\n[Circolare 285, Parte Prima, Titolo I] Le disposizioni di vigilanza prudenziale perseguono la sana e prudente gestione degli intermediari.\n\nDomanda: Qual e il principio prudenziale richiamato dal passaggio?",
            "Il passaggio richiama la sana e prudente gestione come finalita delle disposizioni di vigilanza prudenziale. La risposta non puo estendersi ad altri obblighi non recuperati.",
            "Circolare 285 - Parte Prima, Titolo I",
        ),
        (
            "Contesto recuperato:\n[IFRS 9, par. 5.5] Le perdite attese su crediti sono rilevate secondo un modello di impairment basato sulle expected credit losses.\n\nDomanda: Che informazione ristretta si puo fornire su IFRS 9?",
            "Il passaggio consente solo di affermare che l'impairment IFRS 9 si basa su un modello di perdite attese su crediti. Non supporta una panoramica completa di IFRS 9.",
            "IFRS 9 - par. 5.5",
        ),
        (
            "Contesto recuperato:\n[CRR, art. 4] Il default e richiamato nell'ambito delle esposizioni e del rischio di credito.\n\nDomanda: Come trattare il concetto di default nel corpus recuperato?",
            "Il contesto consente di trattare il default solo come elemento connesso alle esposizioni e al rischio di credito. Non consente di ricostruire tutte le definizioni applicabili nei diversi regimi.",
            "CRR - art. 4",
        ),
        (
            "Contesto recuperato:\n[Basel III, sezione capital framework] Le riforme post-crisi mirano a rafforzare qualita e quantita del capitale bancario.\n\nDomanda: Quale messaggio prudenziale limitato emerge dal documento Basel recuperato?",
            "Il passaggio recuperato consente di indicare che le riforme post-crisi mirano a rafforzare qualita e quantita del capitale bancario. Non supporta un riassunto completo del framework Basel.",
            "Basel III - capital framework",
        ),
        (
            "Contesto recuperato:\n[Circolare 285, aggiornamento 51/2026] Il testo modifica specifiche disposizioni prudenziali, rinviando al documento ufficiale per il dettaglio delle parti interessate.\n\nDomanda: Posso dire che l'aggiornamento 51 modifica disposizioni prudenziali?",
            "Si. Il contesto consente di affermare che l'aggiornamento modifica specifiche disposizioni prudenziali. Non consente di elencare tutte le modifiche se non sono recuperate nel dettaglio.",
            "Circolare 285 - Aggiornamento 51/2026",
        ),
        (
            "Contesto recuperato:\n[Circolare 285, controlli interni] Le funzioni aziendali di controllo concorrono alla gestione e al presidio dei rischi.\n\nDomanda: Quale ruolo emerge per le funzioni di controllo?",
            "Il passaggio indica che le funzioni aziendali di controllo concorrono alla gestione e al presidio dei rischi. La risposta deve restare su questo livello senza inventare compiti ulteriori.",
            "Circolare 285 - controlli interni",
        ),
        (
            "Contesto recuperato:\n[CRR, art. 26] Gli elementi del capitale primario di classe 1 sono individuati secondo condizioni specifiche previste dal regolamento.\n\nDomanda: Che cosa si puo dire sul CET1 dal passaggio?",
            "Il contesto consente di dire che il capitale primario di classe 1 e composto da elementi individuati dal CRR secondo condizioni specifiche. Non supporta l'elenco completo se non recuperato.",
            "CRR - art. 26",
        ),
        (
            "Contesto recuperato:\n[Circolare 285, governo societario] L'organo con funzione di supervisione strategica approva gli indirizzi strategici e verifica la coerenza dell'assetto organizzativo.\n\nDomanda: Quale indicazione di governance emerge?",
            "Il passaggio attribuisce all'organo con funzione di supervisione strategica l'approvazione degli indirizzi strategici e la verifica della coerenza dell'assetto organizzativo.",
            "Circolare 285 - governo societario",
        ),
        (
            "Contesto recuperato:\n[CRR, art. 395] Sono previsti limiti alle grandi esposizioni rispetto al capitale ammissibile dell'ente.\n\nDomanda: Quale informazione prudenziale ristretta si puo dare sulle grandi esposizioni?",
            "Il contesto consente di affermare che il CRR prevede limiti alle grandi esposizioni rapportati al capitale ammissibile dell'ente. Non consente ulteriori dettagli quantitativi se non recuperati.",
            "CRR - art. 395",
        ),
        (
            "Contesto recuperato:\n[IFRS 9, par. 4.1] La classificazione delle attivita finanziarie dipende dal modello di business e dalle caratteristiche dei flussi finanziari contrattuali.\n\nDomanda: Qual e il criterio IFRS 9 citabile dal contesto?",
            "Il contesto consente di indicare che la classificazione delle attivita finanziarie dipende dal modello di business e dalle caratteristiche dei flussi finanziari contrattuali. Non supporta una tabella completa di classificazione.",
            "IFRS 9 - par. 4.1",
        ),
    ]
    for index, (query, answer, source) in enumerate(in_scope, start=1):
        rows.append(make_record(system, f"fio-v2-gnd-{index:03d}", "in_scope_grounded", query, grounded(answer, source)))

    return rows


def main() -> int:
    rows = build_rows()
    ids = [str(row["id"]) for row in rows]
    duplicates = [case_id for case_id, count in Counter(ids).items() if count > 1]
    if duplicates:
        raise RuntimeError(f"Duplicate ids: {duplicates}")

    OUT_DATASET.parent.mkdir(parents=True, exist_ok=True)
    with OUT_DATASET.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    counts = Counter(str(row["category"]) for row in rows)
    total = len(rows)
    OUT_CARD.write_text(
        "\n".join(
            [
                "# Fiorell.IA Supervised V2 Behavior Hardening",
                "",
                f"Rows: {total}",
                "",
                "## Distribution",
                "",
                *[f"- `{category}`: {count} ({count / total:.1%})" for category, count in sorted(counts.items())],
                "",
                "## Intent",
                "",
                "- Reinforces unsupported-source abstention with broad, current, bank-specific and adversarial requests.",
                "- Reinforces out-of-scope refusal for investment, trading, tax, HR, legal and market-data requests.",
                "- Keeps in-scope examples narrow and explicitly grounded in a retrieved context block.",
                "",
                "## Output",
                "",
                f"- `{OUT_DATASET.relative_to(ROOT)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"dataset": str(OUT_DATASET), "rows": total, "categories": counts}, ensure_ascii=False, default=dict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
