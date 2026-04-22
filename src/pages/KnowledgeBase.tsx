import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, FileText, ExternalLink, ArrowRight, BookOpen } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { AppSidebar } from "@/components/AppSidebar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import {
  REG_CATEGORIES,
  RegCategory,
  RegulatoryDoc,
  regulatoryDocs,
} from "@/data/regulatoryDocs";

const categoryStyles: Record<RegCategory, string> = {
  CRR: "bg-primary/10 text-primary border-primary/20",
  IFRS9: "bg-success/10 text-success border-success/25",
  "Basel IV": "bg-warning/10 text-warning border-warning/25",
  EBA: "bg-accent/10 text-accent-foreground border-accent/30",
};

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

const KnowledgeBase = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [activeCat, setActiveCat] = useState<RegCategory | "ALL">("ALL");
  const [selected, setSelected] = useState<RegulatoryDoc | null>(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return regulatoryDocs.filter((d) => {
      if (activeCat !== "ALL" && d.category !== activeCat) return false;
      if (!q) return true;
      return (
        d.title.toLowerCase().includes(q) ||
        d.article.toLowerCase().includes(q) ||
        d.category.toLowerCase().includes(q) ||
        d.abstract.toLowerCase().includes(q)
      );
    });
  }, [query, activeCat]);

  const handleAskAbout = (doc: RegulatoryDoc) => {
    sessionStorage.setItem(
      "genisia.prefillQuestion",
      `${doc.article} — ${doc.title}: `,
    );
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-background">
      <AppHeader modelStatus="loading" indexStatus="warning" />
      <SidebarProvider>
        <div className="mx-auto flex w-full max-w-[1600px]">
          <AppSidebar />
          <main className="min-w-0 flex-1 px-4 py-6 lg:px-8 lg:py-8">
            <div className="mb-5 flex items-center gap-3">
              <SidebarTrigger className="h-8 w-8" />
              <div>
                <h2 className="flex items-center gap-2 text-lg font-semibold tracking-tight text-foreground">
                  <BookOpen className="h-5 w-5 text-primary" />
                  Knowledge Base normativa
                </h2>
                <p className="text-xs text-muted-foreground">
                  Riferimenti regolamentari curati: CRR, IFRS 9, Basel IV, EBA Guidelines.
                </p>
              </div>
            </div>

            <div className="panel-elevated mb-5 p-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div className="relative flex-1">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Cerca per titolo, articolo (es. Art. 92) o categoria…"
                    className="pl-9"
                  />
                </div>
                <div className="flex flex-wrap items-center gap-1.5">
                  <button
                    onClick={() => setActiveCat("ALL")}
                    className={cn(
                      "rounded-md border px-2.5 py-1 text-xs font-medium transition-colors",
                      activeCat === "ALL"
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-border bg-card text-muted-foreground hover:text-foreground",
                    )}
                  >
                    Tutte
                  </button>
                  {REG_CATEGORIES.map((c) => (
                    <button
                      key={c}
                      onClick={() => setActiveCat(c)}
                      className={cn(
                        "rounded-md border px-2.5 py-1 text-xs font-medium transition-colors",
                        activeCat === c
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border bg-card text-muted-foreground hover:text-foreground",
                      )}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>
              <div className="mt-3 text-[11px] text-muted-foreground">
                {filtered.length} {filtered.length === 1 ? "documento" : "documenti"} su{" "}
                {regulatoryDocs.length}
              </div>
            </div>

            {filtered.length === 0 ? (
              <div className="panel p-10 text-center">
                <FileText className="mx-auto h-8 w-8 text-muted-foreground" />
                <p className="mt-3 text-sm font-medium text-foreground">
                  Nessun risultato
                </p>
                <p className="text-xs text-muted-foreground">
                  Modifica i filtri o la query per trovare un riferimento normativo.
                </p>
              </div>
            ) : (
              <ul className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {filtered.map((d) => (
                  <li key={d.id}>
                    <button
                      onClick={() => setSelected(d)}
                      className="panel group flex h-full w-full flex-col items-start gap-3 p-4 text-left transition-all hover:border-primary/40 hover:shadow-md"
                    >
                      <div className="flex w-full items-start justify-between gap-2">
                        <span
                          className={cn(
                            "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium",
                            categoryStyles[d.category],
                          )}
                        >
                          {d.category}
                        </span>
                        <span className="font-mono text-[11px] text-muted-foreground">
                          {d.article}
                        </span>
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-foreground group-hover:text-primary">
                          {d.title}
                        </h3>
                        <p className="mt-1 line-clamp-3 text-xs leading-relaxed text-muted-foreground">
                          {d.abstract}
                        </p>
                      </div>
                      <div className="mt-auto flex w-full items-center justify-between border-t border-border pt-2 text-[11px] text-muted-foreground">
                        <span>Aggiornato {formatDate(d.updated)}</span>
                        <span className="inline-flex items-center gap-1 text-primary opacity-0 transition-opacity group-hover:opacity-100">
                          Dettagli <ArrowRight className="h-3 w-3" />
                        </span>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </main>
        </div>
      </SidebarProvider>

      <Sheet open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <SheetContent side="right" className="w-full sm:max-w-lg overflow-y-auto">
          {selected && (
            <>
              <SheetHeader>
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium",
                      categoryStyles[selected.category],
                    )}
                  >
                    {selected.category}
                  </span>
                  <span className="font-mono text-xs text-muted-foreground">
                    {selected.article}
                  </span>
                </div>
                <SheetTitle className="text-left">{selected.title}</SheetTitle>
                <SheetDescription className="text-left">
                  Aggiornato {formatDate(selected.updated)}
                </SheetDescription>
              </SheetHeader>

              <div className="mt-6 space-y-5">
                <section>
                  <h4 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Sintesi normativa
                  </h4>
                  <p className="text-sm leading-relaxed text-foreground">
                    {selected.abstract}
                  </p>
                </section>

                <section className="rounded-md border border-border bg-secondary/40 p-3">
                  <h4 className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Citazione fonte
                  </h4>
                  <p className="font-mono text-xs leading-relaxed text-foreground">
                    {selected.citation}
                  </p>
                  {selected.url && (
                    <a
                      href={selected.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-flex items-center gap-1 text-xs text-primary hover:underline"
                    >
                      Apri fonte ufficiale <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </section>

                <div className="flex flex-col gap-2 sm:flex-row">
                  <Button
                    onClick={() => handleAskAbout(selected)}
                    className="flex-1 gap-1.5"
                  >
                    Interroga su questo articolo <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="outline" onClick={() => setSelected(null)}>
                    Chiudi
                  </Button>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
};

export default KnowledgeBase;
