import { AnswerData } from "@/components/AnswerPanel";
import { KnowledgeDoc } from "@/components/DocumentLibrary";

export const mockDocs: KnowledgeDoc[] = [
  {
    id: "ifrs9",
    title: "IFRS 9 — Strumenti finanziari",
    source: "IASB",
    pages: 184,
    chunks: 612,
    status: "indexed",
    updated: "2 giorni fa",
  },
  {
    id: "crr",
    title: "Regolamento UE 575/2013 (CRR)",
    source: "EUR-Lex",
    pages: 337,
    chunks: 1248,
    status: "indexed",
    updated: "5 giorni fa",
  },
  {
    id: "crr2",
    title: "Regolamento UE 2019/876 (CRR II)",
    source: "EUR-Lex",
    pages: 252,
    chunks: 941,
    status: "indexed",
    updated: "1 settimana fa",
  },
  {
    id: "eba-gl",
    title: "EBA/GL/2017/06 — Pratiche di gestione del rischio di credito",
    source: "EBA",
    pages: 48,
    chunks: 174,
    status: "indexed",
    updated: "2 settimane fa",
  },
  {
    id: "basel",
    title: "Basel III: Finalising post-crisis reforms",
    source: "BIS",
    pages: 162,
    chunks: 0,
    status: "pending",
    updated: "in elaborazione",
  },
];

export const mockAnswer = (question: string): AnswerData => ({
  question,
  model: "llama3.1:8b",
  generatedAt: new Date().toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" }),
  confidence: "high",
  answer: `Secondo il principio contabile IFRS 9, il passaggio dallo Stage 1 allo Stage 2 si verifica quando si registra un aumento significativo del rischio di credito (SICR) di un'esposizione finanziaria rispetto al momento della rilevazione iniziale.

La valutazione del SICR deve essere effettuata su base individuale o collettiva, considerando informazioni ragionevoli e supportabili, comprese quelle prospettiche (forward-looking). Gli indicatori principali includono variazioni significative della probabilità di default lifetime, downgrade interni o esterni, modifiche delle condizioni contrattuali e la presenza di esposizioni scadute da oltre 30 giorni (presunzione confutabile).

Una volta classificata in Stage 2, l'esposizione richiede la rilevazione di una perdita attesa lungo l'intera vita residua dello strumento (lifetime ECL), in luogo della ECL a 12 mesi prevista per lo Stage 1. La banca deve documentare metodologia, soglie quantitative e processo di governance per la determinazione del SICR.`,
  sources: [
    {
      id: "s1",
      document: "IFRS 9 — Strumenti finanziari",
      reference: "§ 5.5.9",
      page: 47,
      score: 0.92,
      excerpt:
        "An entity shall measure the loss allowance for a financial instrument at an amount equal to the lifetime expected credit losses if the credit risk on that financial instrument has increased significantly since initial recognition.",
    },
    {
      id: "s2",
      document: "IFRS 9 — Strumenti finanziari",
      reference: "App. B, § B5.5.17",
      page: 112,
      score: 0.87,
      excerpt:
        "The assessment of significant increases in credit risk should consider reasonable and supportable forward-looking information that is available without undue cost or effort, including macroeconomic factors.",
    },
    {
      id: "s3",
      document: "EBA/GL/2017/06",
      reference: "§ 5.3.2",
      page: 22,
      score: 0.78,
      excerpt:
        "Le istituzioni dovrebbero stabilire una metodologia chiara e documentata per identificare l'aumento significativo del rischio di credito, includendo indicatori quantitativi e qualitativi appropriati al portafoglio di riferimento.",
    },
    {
      id: "s4",
      document: "Regolamento UE 575/2013 (CRR)",
      reference: "Art. 178",
      page: 198,
      score: 0.64,
      excerpt:
        "Si considera che un'esposizione sia in stato di default quando il debitore è in arretrato da oltre 90 giorni su una qualsiasi obbligazione creditizia rilevante verso l'ente o il gruppo bancario.",
    },
  ],
});
