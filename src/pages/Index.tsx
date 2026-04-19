import { useState } from "react";
import { FileStack, Layers, Cpu, Database, PanelLeftClose, PanelLeft } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { ConfigSidebar, AssistantConfig } from "@/components/ConfigSidebar";
import { MetricCard } from "@/components/MetricCard";
import { AskBox } from "@/components/AskBox";
import { AnswerPanel, AnswerData } from "@/components/AnswerPanel";
import { AnswerSkeleton } from "@/components/AnswerSkeleton";
import { EmptyState } from "@/components/EmptyState";
import { DocumentLibrary } from "@/components/DocumentLibrary";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { mockDocs, mockAnswer } from "@/data/mockData";
import { toast } from "@/hooks/use-toast";

const Index = () => {
  const [config, setConfig] = useState<AssistantConfig>({
    model: "llama3.1:8b",
    topK: 5,
    chunkSize: 768,
    overlap: 120,
    fastMode: false,
  });
  const [answer, setAnswer] = useState<AnswerData | null>(null);
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const indexedDocs = mockDocs.filter((d) => d.status === "indexed");
  const totalChunks = indexedDocs.reduce((acc, d) => acc + d.chunks, 0);

  const handleAsk = (q: string) => {
    setLoading(true);
    setAnswer(null);
    setTimeout(() => {
      setAnswer(mockAnswer(q));
      setLoading(false);
    }, 1400);
  };

  const handleRebuild = () => {
    toast({
      title: "Ricostruzione indice avviata",
      description: "L'operazione viene eseguita in background. Riceverai una notifica al completamento.",
    });
  };

  const setupSteps = [
    { label: "Verifica runtime locale", description: "Modello LLM e servizio embeddings raggiungibili.", done: true },
    { label: "Carica documenti normativi", description: "Importa PDF di IFRS 9, CRR e linee guida EBA.", done: indexedDocs.length > 0 },
    { label: "Costruisci indice vettoriale", description: "Chunking, embedding e persistenza dell'indice.", done: totalChunks > 0 },
    { label: "Configura parametri di recupero", description: "Top-K, dimensione chunk e modalità rapida.", done: true },
  ];

  return (
    <div className="min-h-screen bg-background">
      <AppHeader modelStatus="online" indexStatus="online" />

      <div className="mx-auto flex max-w-[1600px]">
        {/* Desktop sidebar */}
        <div
          className={`hidden shrink-0 border-r border-border bg-card transition-all duration-200 lg:block ${
            sidebarOpen ? "w-[300px]" : "w-0 overflow-hidden"
          }`}
        >
          {sidebarOpen && (
            <div className="sticky top-[57px] h-[calc(100vh-57px)]">
              <ConfigSidebar config={config} onChange={setConfig} onRebuildIndex={handleRebuild} />
            </div>
          )}
        </div>

        {/* Main */}
        <main className="min-w-0 flex-1 px-4 py-6 lg:px-8 lg:py-8">
          {/* Top bar */}
          <div className="mb-5 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              {/* Desktop toggle */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="hidden h-8 w-8 p-0 lg:flex"
                aria-label="Toggle sidebar"
              >
                {sidebarOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeft className="h-4 w-4" />}
              </Button>
              {/* Mobile sidebar */}
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline" size="sm" className="h-8 gap-1.5 lg:hidden">
                    <PanelLeft className="h-3.5 w-3.5" /> Configurazione
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="w-[320px] p-0">
                  <ConfigSidebar config={config} onChange={setConfig} onRebuildIndex={handleRebuild} />
                </SheetContent>
              </Sheet>
              <div>
                <h2 className="text-lg font-semibold tracking-tight text-foreground">Assistente</h2>
                <p className="text-xs text-muted-foreground">
                  Interroga la base normativa con risposte tracciabili.
                </p>
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <MetricCard
              icon={FileStack}
              label="Documenti indicizzati"
              value={indexedDocs.length}
              hint={`su ${mockDocs.length} totali`}
              tone="info"
            />
            <MetricCard
              icon={Layers}
              label="Chunk indicizzati"
              value={totalChunks.toLocaleString()}
              hint={`chunk size ${config.chunkSize}`}
            />
            <MetricCard
              icon={Cpu}
              label="Modello attivo"
              value={config.model}
              hint={config.fastMode ? "modalità rapida" : "modalità standard"}
              tone="success"
            />
            <MetricCard
              icon={Database}
              label="Top-K retrieval"
              value={config.topK}
              hint={`overlap ${config.overlap}`}
            />
          </div>

          {/* Empty state shown above ask box when no answer yet */}
          {!answer && !loading && (
            <div className="mb-5">
              <EmptyState steps={setupSteps} />
            </div>
          )}

          {/* Ask */}
          <div className="mb-5">
            <AskBox onAsk={handleAsk} isLoading={loading} />
          </div>

          {/* Answer / loading */}
          {loading && <AnswerSkeleton />}
          {answer && !loading && <AnswerPanel data={answer} />}

          {/* Library */}
          <div className="mt-8">
            <div className="mb-3 flex items-baseline justify-between">
              <h2 className="text-sm font-semibold text-foreground">Knowledge base</h2>
              <span className="text-[11px] text-muted-foreground">
                {indexedDocs.length} documenti · {totalChunks.toLocaleString()} chunk
              </span>
            </div>
            <DocumentLibrary
              docs={mockDocs}
              onImport={() => toast({ title: "Importazione PDF", description: "Seleziona uno o più documenti normativi da indicizzare." })}
              onDownload={() => toast({ title: "Download preset", description: "Pacchetto IFRS 9 + CRR scaricato dall'archivio interno." })}
            />
          </div>

          <footer className="mt-10 border-t border-border pt-5 text-[11px] text-muted-foreground">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span>
                Gen.Is.IA · Strumento interno per analisi normativa · Le risposte richiedono validazione professionale.
              </span>
              <span className="font-mono">v0.1 · build offline</span>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
};

export default Index;
