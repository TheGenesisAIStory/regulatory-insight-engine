export type RegCategory = "CRR" | "IFRS9" | "Basel IV" | "EBA";

export interface RegulatoryDoc {
  id: string;
  title: string;
  article: string;
  category: RegCategory;
  updated: string; // ISO date
  abstract: string;
  citation: string;
  url?: string;
}

export const regulatoryDocs: RegulatoryDoc[] = [
  {
    id: "crr-art-92",
    title: "Requisiti di fondi propri",
    article: "CRR Art. 92",
    category: "CRR",
    updated: "2024-01-09",
    abstract:
      "Definisce i coefficienti minimi di capitale che gli enti devono soddisfare in via continuativa: CET1 ratio 4,5%, Tier 1 ratio 6%, Total Capital ratio 8% degli importi delle esposizioni ponderate per il rischio (RWA).",
    citation:
      "Regolamento (UE) n. 575/2013 (CRR), Articolo 92 — Requisiti di fondi propri.",
    url: "https://eur-lex.europa.eu/eli/reg/2013/575/oj",
  },
  {
    id: "crr-art-134",
    title: "Esposizioni ad alto rischio e ponderazioni speciali",
    article: "CRR Art. 134",
    category: "CRR",
    updated: "2023-11-22",
    abstract:
      "Disciplina le ponderazioni applicabili ad altre poste, fra cui partecipazioni in capitale, esposizioni in valuta non locale, oro, partite in corso di lavorazione e immobilizzazioni materiali, sotto il metodo standardizzato.",
    citation: "Regolamento (UE) n. 575/2013 (CRR), Articolo 134.",
  },
  {
    id: "crr-art-178",
    title: "Definizione di default di un debitore",
    article: "CRR Art. 178",
    category: "CRR",
    updated: "2023-09-15",
    abstract:
      "Stabilisce i criteri per identificare un'esposizione in default: scaduto da oltre 90 giorni rispetto a una soglia di materialità, oppure unlikeliness to pay (UTP) basata su indicatori qualitativi e quantitativi.",
    citation: "Regolamento (UE) n. 575/2013 (CRR), Articolo 178.",
  },
  {
    id: "crr-art-197",
    title: "Strumenti di garanzia reale finanziaria ammissibili",
    article: "CRR Art. 197",
    category: "CRR",
    updated: "2024-02-04",
    abstract:
      "Elenca le tipologie di collateral finanziari ammissibili ai fini della Credit Risk Mitigation (CRM): contante, titoli di debito con rating qualificato, azioni quotate in indici principali, oro e quote di OICR ammissibili.",
    citation: "Regolamento (UE) n. 575/2013 (CRR), Articolo 197.",
  },
  {
    id: "crr-art-395",
    title: "Limiti alla concentrazione delle grandi esposizioni",
    article: "CRR Art. 395",
    category: "CRR",
    updated: "2023-10-30",
    abstract:
      "Vincolo del 25% dei fondi propri Tier 1 per singolo cliente o gruppo connesso, con soglia ridotta per esposizioni verso altri G-SII e O-SII. Definisce la disciplina di monitoraggio e segnalazione.",
    citation: "Regolamento (UE) n. 575/2013 (CRR), Articolo 395.",
  },
  {
    id: "ifrs9-stage-classification",
    title: "Classificazione in Stage 1, 2 e 3",
    article: "IFRS 9 §5.5",
    category: "IFRS9",
    updated: "2024-03-12",
    abstract:
      "Modello a tre stadi per l'impairment: Stage 1 (12-month ECL su esposizioni performing), Stage 2 (lifetime ECL in caso di SICR), Stage 3 (lifetime ECL su esposizioni credit-impaired). I criteri di transizione devono essere coerenti con il risk management interno.",
    citation: "IFRS 9 — Financial Instruments, paragrafi 5.5.1 — 5.5.20.",
  },
  {
    id: "ifrs9-ecl",
    title: "Misurazione delle Expected Credit Losses",
    article: "IFRS 9 §5.5.17",
    category: "IFRS9",
    updated: "2024-03-12",
    abstract:
      "Le ECL sono stimate come media ponderata per la probabilità delle perdite di credito attese, attualizzate al tasso di interesse effettivo originario, considerando informazioni ragionevoli e supportabili, incluse le forward-looking information.",
    citation: "IFRS 9 — Financial Instruments, paragrafo 5.5.17.",
  },
  {
    id: "ifrs9-sicr",
    title: "Significant Increase in Credit Risk (SICR)",
    article: "IFRS 9 §5.5.9",
    category: "IFRS9",
    updated: "2024-03-12",
    abstract:
      "La transizione a Stage 2 richiede una valutazione comparativa fra la PD lifetime alla data di reporting e quella stimata all'origine. Indicatori quantitativi (variazione PD), qualitativi (watch-list) e backstop dei 30 giorni di scaduto sono complementari.",
    citation: "IFRS 9 — Financial Instruments, paragrafi 5.5.9 — 5.5.11.",
  },
  {
    id: "ifrs9-poci",
    title: "Esposizioni Purchased or Originated Credit-Impaired (POCI)",
    article: "IFRS 9 §5.5.13",
    category: "IFRS9",
    updated: "2024-03-12",
    abstract:
      "Per le POCI l'ECL lifetime è incorporata nel tasso di interesse effettivo credit-adjusted alla rilevazione iniziale. Le successive variazioni cumulative dell'ECL lifetime sono rilevate a conto economico.",
    citation: "IFRS 9 — Financial Instruments, paragrafo 5.5.13 — 5.5.14.",
  },
  {
    id: "basel-iv-output-floor",
    title: "Output floor del 72,5%",
    article: "Basel IV — CRE 32",
    category: "Basel IV",
    updated: "2024-01-01",
    abstract:
      "L'output floor limita il beneficio dei modelli interni: gli RWA totali non possono essere inferiori al 72,5% degli RWA calcolati con il metodo standardizzato. Phase-in graduale dal 50% (2025) al 72,5% (2030).",
    citation: "Basel III: Finalising post-crisis reforms (BCBS, dic. 2017), CRE 32.",
  },
  {
    id: "basel-iv-sa-ccr",
    title: "SA-CCR — Standardised Approach for Counterparty Credit Risk",
    article: "Basel IV — CRE 52",
    category: "Basel IV",
    updated: "2023-07-18",
    abstract:
      "Sostituisce il Current Exposure Method per il calcolo dell'EAD su derivati OTC. EAD = alpha × (Replacement Cost + Potential Future Exposure), con alpha = 1,4 e PFE differenziata per asset class.",
    citation: "BCBS — The standardised approach for measuring counterparty credit risk exposures, CRE 52.",
  },
  {
    id: "basel-iv-frtb",
    title: "FRTB — Fundamental Review of the Trading Book",
    article: "Basel IV — MAR 20",
    category: "Basel IV",
    updated: "2024-01-01",
    abstract:
      "Nuovo framework per il rischio di mercato: confine trading/banking book più rigido, Internal Models Approach (IMA) basato su Expected Shortfall al 97,5% e Standardised Approach (SA) granulare per fattori di rischio.",
    citation: "BCBS — Minimum capital requirements for market risk (MAR 20-99).",
  },
  {
    id: "eba-lom",
    title: "EBA Guidelines on Loan Origination and Monitoring",
    article: "EBA/GL/2020/06",
    category: "EBA",
    updated: "2021-06-30",
    abstract:
      "Definisce standard di governance per l'erogazione del credito: assessment del merito creditizio, valutazione del collateral, ESG factors, pricing risk-based e monitoring continuo del portafoglio performing.",
    citation: "EBA/GL/2020/06 — Guidelines on loan origination and monitoring.",
  },
  {
    id: "eba-npl-management",
    title: "EBA Guidelines on management of non-performing exposures",
    article: "EBA/GL/2018/06",
    category: "EBA",
    updated: "2019-06-30",
    abstract:
      "Strategia NPE: target operativi pluriennali di riduzione, governance dedicata (NPE workout unit), early warning indicators, opzioni di forbearance e criteri di write-off coerenti con la disciplina prudenziale.",
    citation: "EBA/GL/2018/06 — Guidelines on management of non-performing and forborne exposures.",
  },
  {
    id: "eba-icaap-ilaap",
    title: "EBA Guidelines on ICAAP and ILAAP information",
    article: "EBA/GL/2016/10",
    category: "EBA",
    updated: "2017-01-01",
    abstract:
      "Specifica le informazioni che le banche devono fornire alle autorità competenti su ICAAP e ILAAP per supportare lo SREP, inclusi modelli di capitale interno, stress test e governance del risk appetite framework.",
    citation: "EBA/GL/2016/10 — Guidelines on ICAAP and ILAAP information collected for SREP.",
  },
  {
    id: "crr-art-429-lr",
    title: "Leverage Ratio",
    article: "CRR Art. 429",
    category: "CRR",
    updated: "2023-12-01",
    abstract:
      "Rapporto fra capitale Tier 1 ed esposizione complessiva (on e off balance sheet, derivati e SFT), con requisito minimo del 3% e buffer aggiuntivo per le G-SII.",
    citation: "Regolamento (UE) n. 575/2013 (CRR), Articolo 429.",
  },
];

export const REG_CATEGORIES: RegCategory[] = ["CRR", "IFRS9", "Basel IV", "EBA"];
