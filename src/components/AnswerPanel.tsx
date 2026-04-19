import { FileText, FileType2, FileDown, AlertTriangle, BookMarked, Quote, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

export interface RetrievedSource {
  id: string;
  document: string;
  reference: string;
  page: number;
  score: number;
  excerpt: string;
}

export interface AnswerData {
  question: string;
  answer: string;
  confidence: "high" | "medium" | "low";
  sources: RetrievedSource[];
  generatedAt: string;
  model: string;
}

interface AnswerPanelProps {
  data: AnswerData;
}

const confidenceMeta = {
  high: { label: "Confidenza alta", tone: "bg-success/10 text-success border-success/20" },
  medium: { label: "Confidenza media", tone: "bg-warning/10 text-warning border-warning/25" },
  low: { label: "Confidenza limitata", tone: "bg-destructive/10 text-destructive border-destructive/25" },
};

export const AnswerPanel = ({ data }: AnswerPanelProps) => {
  const [expanded, setExpanded] = useState<string | null>(data.sources[0]?.id ?? null);

  const handleExport = (format: string) => {
    toast({
      title: `Export ${format} avviato`,
      description: "Il file sarà disponibile al termine della generazione.",
    });
  };

  const conf = confidenceMeta[data.confidence];

  return (
    <div className="space-y-4">
      {/* Answer card */}
      <article className="panel-elevated overflow-hidden">
        <header className="flex flex-wrap items-start justify-between gap-3 border-b border-border bg-secondary/30 px-5 py-3">
          <div className="min-w-0 flex-1">
            <div className="mb-0.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              Risposta
            </div>
            <h2 className="line-clamp-2 text-sm font-medium text-foreground">{data.question}</h2>
          </div>
          <span className={cn("shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-medium", conf.tone)}>
            {conf.label}
          </span>
        </header>

        <div className="px-5 py-5">
          {data.confidence === "low" && (
            <div className="mb-4 flex items-start gap-3 rounded-md border border-warning/30 bg-warning/5 p-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
              <p className="text-xs leading-relaxed text-foreground">
                Il contesto recuperato è limitato. La risposta potrebbe non essere completa.
                Si consiglia di consultare le fonti citate o di ampliare la base documentale.
              </p>
            </div>
          )}

          <div className="prose prose-sm max-w-none text-sm leading-relaxed text-foreground">
            {data.answer.split("\n\n").map((para, i) => (
              <p key={i} className="mb-3 last:mb-0">{para}</p>
            ))}
          </div>

          <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
            <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
              <span className="font-mono">{data.model}</span>
              <span className="h-3 w-px bg-border" />
              <span>{data.sources.length} fonti utilizzate</span>
              <span className="h-3 w-px bg-border" />
              <span>{data.generatedAt}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs" onClick={() => handleExport("PDF")}>
                <FileType2 className="h-3.5 w-3.5" /> PDF
              </Button>
              <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs" onClick={() => handleExport("DOCX")}>
                <FileText className="h-3.5 w-3.5" /> DOCX
              </Button>
              <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs" onClick={() => handleExport("TXT")}>
                <FileDown className="h-3.5 w-3.5" /> TXT
              </Button>
            </div>
          </div>
        </div>
      </article>

      {/* Sources */}
      <section className="panel overflow-hidden">
        <header className="flex items-center justify-between border-b border-border bg-secondary/30 px-5 py-3">
          <div className="flex items-center gap-2">
            <BookMarked className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Fonti recuperate</h3>
            <span className="rounded-full bg-secondary px-2 py-0.5 font-mono text-[10px] text-muted-foreground">
              {data.sources.length}
            </span>
          </div>
          <span className="text-[11px] text-muted-foreground">
            Ordinate per rilevanza
          </span>
        </header>
        <ul className="divide-y divide-border">
          {data.sources.map((src, idx) => {
            const open = expanded === src.id;
            return (
              <li key={src.id}>
                <button
                  onClick={() => setExpanded(open ? null : src.id)}
                  className="flex w-full items-start gap-3 px-5 py-3 text-left transition-colors hover:bg-secondary/40"
                >
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-primary/10 font-mono text-[11px] font-semibold text-primary">
                    {idx + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                      <span className="text-sm font-medium text-foreground">{src.document}</span>
                      <span className="font-mono text-[11px] text-muted-foreground">
                        {src.reference} · p.{src.page}
                      </span>
                    </div>
                    <div className="mt-0.5 flex items-center gap-2 text-[11px] text-muted-foreground">
                      <span>Rilevanza</span>
                      <div className="h-1 w-20 overflow-hidden rounded-full bg-secondary">
                        <div
                          className="h-full bg-primary"
                          style={{ width: `${Math.round(src.score * 100)}%` }}
                        />
                      </div>
                      <span className="font-mono">{(src.score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <ChevronDown className={cn("mt-1 h-4 w-4 text-muted-foreground transition-transform", open && "rotate-180")} />
                </button>
                {open && (
                  <div className="border-t border-border bg-secondary/30 px-5 py-4">
                    <div className="flex items-start gap-3">
                      <Quote className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                      <blockquote className="border-l-2 border-primary/40 pl-4 text-sm italic leading-relaxed text-foreground">
                        {src.excerpt}
                      </blockquote>
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </section>
    </div>
  );
};
