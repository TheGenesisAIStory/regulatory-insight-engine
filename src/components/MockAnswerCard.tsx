import { BookMarked, FileText, Sparkles } from "lucide-react";

const MOCK_SOURCES = [
  { document: "IFRS9.pdf", reference: "Stage 2 / lifetime ECL", score: "82%" },
  { document: "CRR.pdf", reference: "Art. 178 default", score: "74%" },
];

export const MockAnswerCard = () => {
  return (
    <article className="panel overflow-hidden">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-border bg-secondary/30 px-5 py-3">
        <div className="min-w-0">
          <div className="mb-0.5 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5" />
            Esempio statico
          </div>
          <h3 className="text-sm font-semibold text-foreground">
            Come apparira' una risposta tracciabile
          </h3>
        </div>
        <span className="rounded-full border border-border bg-card px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
          Preview
        </span>
      </header>

      <div className="space-y-4 px-5 py-4">
        <p className="text-sm leading-relaxed text-foreground">
          Il sistema sintetizza solo il contesto recuperato dalla knowledge base locale e mostra le fonti
          utilizzate per verificare il passaggio normativo o contabile.
        </p>

        <div className="grid gap-2 sm:grid-cols-2">
          {MOCK_SOURCES.map((source, index) => (
            <div key={source.document} className="rounded-md border border-border bg-secondary/30 p-3">
              <div className="flex items-start gap-2">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-primary/10 font-mono text-[11px] font-semibold text-primary">
                  {index + 1}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 text-sm font-medium text-foreground">
                    <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                    <span className="truncate">{source.document}</span>
                  </div>
                  <p className="mt-1 text-[11px] text-muted-foreground">{source.reference}</p>
                  <div className="mt-2 flex items-center gap-2 text-[11px] text-muted-foreground">
                    <BookMarked className="h-3.5 w-3.5" />
                    <span>Rilevanza {source.score}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
};
