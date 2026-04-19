import { FileText, Upload, Download, FileCheck2, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface KnowledgeDoc {
  id: string;
  title: string;
  source: string;
  pages: number;
  chunks: number;
  status: "indexed" | "pending" | "error";
  updated: string;
}

interface DocumentLibraryProps {
  docs: KnowledgeDoc[];
  onImport: () => void;
  onDownload: () => void;
  downloadLabel?: string;
}

const statusMeta = {
  indexed: { label: "Indicizzato", tone: "text-success bg-success/10 border-success/20", icon: FileCheck2 },
  pending: { label: "In attesa", tone: "text-warning bg-warning/10 border-warning/25", icon: Clock },
  error: { label: "Errore", tone: "text-destructive bg-destructive/10 border-destructive/25", icon: FileText },
};

export const DocumentLibrary = ({ docs, onImport, onDownload, downloadLabel = "Scarica preset" }: DocumentLibraryProps) => {
  return (
    <section className="panel overflow-hidden">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-secondary/30 px-5 py-3">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Base documentale</h3>
          <p className="text-[11px] text-muted-foreground">
            Documenti normativi indicizzati per il recupero semantico
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs" onClick={onDownload}>
            <Download className="h-3.5 w-3.5" /> {downloadLabel}
          </Button>
          <Button size="sm" className="h-8 gap-1.5 text-xs" onClick={onImport}>
            <Upload className="h-3.5 w-3.5" /> Importa PDF
          </Button>
        </div>
      </header>

      <div className="hidden border-b border-border bg-card px-5 py-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground md:grid md:grid-cols-[1fr_120px_100px_100px_140px]">
        <span>Documento</span>
        <span>Fonte</span>
        <span className="text-right">Pagine</span>
        <span className="text-right">Chunk</span>
        <span className="text-right">Stato</span>
      </div>

      <ul className="divide-y divide-border">
        {docs.map((d) => {
          const meta = statusMeta[d.status];
          const Icon = meta.icon;
          return (
            <li
              key={d.id}
              className="grid grid-cols-1 items-center gap-2 px-5 py-3 transition-colors hover:bg-secondary/40 md:grid-cols-[1fr_120px_100px_100px_140px]"
            >
              <div className="flex items-start gap-3 min-w-0">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border bg-secondary/60">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium text-foreground">{d.title}</div>
                  <div className="text-[11px] text-muted-foreground">Aggiornato {d.updated}</div>
                </div>
              </div>
              <div className="font-mono text-xs text-muted-foreground">{d.source}</div>
              <div className="font-mono text-xs text-foreground md:text-right">{d.pages}</div>
              <div className="font-mono text-xs text-foreground md:text-right">{d.chunks.toLocaleString()}</div>
              <div className="md:text-right">
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium",
                    meta.tone
                  )}
                >
                  <Icon className="h-3 w-3" />
                  {meta.label}
                </span>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
};
