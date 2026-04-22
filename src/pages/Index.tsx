import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileStack, Layers, Cpu, Database, PanelLeftClose, PanelLeft, Library, History, X } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { ConfigSidebar, AssistantConfig } from "@/components/ConfigSidebar";
import { MetricCard } from "@/components/MetricCard";
import { AskBox } from "@/components/AskBox";
import { AnswerPanel, AnswerData } from "@/components/AnswerPanel";
import { AnswerSkeleton } from "@/components/AnswerSkeleton";
import { EmptyState } from "@/components/EmptyState";
import { DocumentLibrary } from "@/components/DocumentLibrary";
import { HistoryPanel } from "@/components/HistoryPanel";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { mockDocs } from "@/data/mockData";
import { toast } from "@/hooks/use-toast";
import { API_BASE_URL, askGenisia, GenisiaApiError, getDocuments, getReadiness, HealthResponse, rebuildIndex } from "@/lib/genisiaApi";
import { todayCount, useHistoryStore } from "@/store/historyStore";


const Index = () => {
  const [config, setConfig] = useState<AssistantConfig>({
    model: "qwen2.5:3b",
    topK: 5,
    chunkSize: 768,
    overlap: 120,
    fastMode: false,
  });
  const [answer, setAnswer] = useState<AnswerData | null>(null);
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [activeHistoryId, setActiveHistoryId] = useState<string | null>(null);
  const [readOnly, setReadOnly] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [apiDocs, setApiDocs] = useState(mockDocs);
  const [apiChecked, setApiChecked] = useState(false);
  const [readinessReasons, setReadinessReasons] = useState<string[]>([]);

  const addHistoryEntry = useHistoryStore((s) => s.addEntry);
  const historyEntries = useHistoryStore((s) => s.entries);
  const todayQueries = todayCount(historyEntries);

  const apiOnline = Boolean(health?.ollamaOnline);
  const usingRealDocs = apiDocs !== mockDocs;
  const indexedDocs = apiDocs.filter((d) => d.status === "indexed");
  const totalChunks = indexedDocs.reduce((acc, d) => acc + d.chunks, 0);

  useEffect(() => {
    let mounted = true;

    const loadRuntimeState = async () => {
      try {
        const [readiness, docs] = await Promise.all([getReadiness(), getDocuments()]);
        if (!mounted) return;
        const healthData = readiness.status;
        setHealth(healthData);
        setReadinessReasons(readiness.reasons);
        const chatModel = healthData.activeChatModel ?? healthData.availableModels.find((model) => !model.toLowerCase().includes("embed"));
        if (chatModel) {
          setConfig((current) => ({
            ...current,
            model: healthData.availableModels.includes(current.model) ? current.model : chatModel,
          }));
        }
        if (docs.length > 0) {
          setApiDocs(docs);
        }
      } catch (error) {
        if (!mounted) return;
        setHealth(null);
        setReadinessReasons([]);
        const message = error instanceof GenisiaApiError ? `${error.message} (${error.status})` : `Avvia il backend su ${API_BASE_URL}.`;
        toast({
          title: "API RAG non raggiungibile",
          description: `${message} La libreria documentale resta in modalita' dimostrativa.`,
          variant: "destructive",
        });
      } finally {
        if (mounted) {
          setApiChecked(true);
        }
      }
    };

    loadRuntimeState();

    return () => {
      mounted = false;
    };
  }, []);

  const handleAsk = async (q: string) => {
    setLoading(true);
    setAnswer(null);
    setActiveHistoryId(null);
    setReadOnly(false);

    try {
      const data = await askGenisia(q, config.topK, config.model);
      setAnswer(data);
      const entry = addHistoryEntry(q, data);
      setActiveHistoryId(entry.id);
    } catch (error) {
      const message = error instanceof GenisiaApiError ? `${error.message} (HTTP ${error.status})` : error instanceof Error ? error.message : "Errore sconosciuto";
      toast({
        title: "Interrogazione non riuscita",
        description: message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRebuild = async () => {
    setLoading(true);
    try {
      const result = await rebuildIndex();
      const docs = await getDocuments();
      setHealth(result.status);
      if (docs.length > 0) {
        setApiDocs(docs);
      }
      toast({
        title: "Indice ricostruito",
        description: `${result.status.chunks.toLocaleString()} chunk indicizzati dal motore RAG locale.`,
      });
    } catch (error) {
      const message = error instanceof GenisiaApiError ? `${error.message} (HTTP ${error.status})` : error instanceof Error ? error.message : "Errore sconosciuto";
      toast({
        title: "Ricostruzione indice non riuscita",
        description: message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const setupSteps = [
    { label: "Verifica runtime locale", description: readinessReasons[0] ?? `API RAG ${API_BASE_URL} e Ollama raggiungibili.`, done: apiOnline },
    { label: "Carica documenti normativi", description: "Importa PDF di IFRS 9, CRR, Basel e Banca d'Italia.", done: indexedDocs.length > 0 },
    { label: "Costruisci indice vettoriale", description: "Chunking, embedding e persistenza dell'indice.", done: Boolean(health?.ready) || totalChunks > 0 },
    { label: "Configura parametri di recupero", description: "Top-K, dimensione chunk e modalità rapida.", done: true },
  ];

  return (
    <div className="min-h-screen bg-background">
      <AppHeader
        modelStatus={!apiChecked ? "loading" : apiOnline ? "online" : "offline"}
        indexStatus={!apiChecked ? "warning" : health?.ready ? "online" : usingRealDocs ? "warning" : "offline"}
      />

      <div className="mx-auto flex max-w-[1600px]">
        {/* Desktop config sidebar */}
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
              {/* Mobile config sidebar */}
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
            <div className="flex items-center gap-1.5">
              {/* History toggle (desktop) */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setHistoryOpen((v) => !v)}
                className="relative hidden h-8 gap-1.5 text-xs lg:flex"
              >
                <History className="h-3.5 w-3.5" />
                Storico
                {todayQueries > 0 && (
                  <span className="ml-1 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-primary px-1 font-mono text-[10px] font-semibold text-primary-foreground">
                    {todayQueries}
                  </span>
                )}
              </Button>
              {/* History toggle (mobile) */}
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline" size="sm" className="relative h-8 gap-1.5 text-xs lg:hidden">
                    <History className="h-3.5 w-3.5" />
                    {todayQueries > 0 && (
                      <span className="absolute -right-1 -top-1 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-primary px-1 font-mono text-[10px] font-semibold text-primary-foreground">
                        {todayQueries}
                      </span>
                    )}
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="w-[340px] p-0">
                  <HistoryPanel
                    activeId={activeHistoryId}
                    onSelect={(e) => {
                      setAnswer(e.answer);
                      setActiveHistoryId(e.id);
                      setReadOnly(true);
                    }}
                  />
                </SheetContent>
              </Sheet>
              <Button asChild variant="outline" size="sm" className="h-8 gap-1.5 text-xs">
                <Link to="/knowledge-base">
                  <Library className="h-3.5 w-3.5" /> Knowledge Base
                </Link>
              </Button>
            </div>
          </div>

          <div className="mb-5 rounded-md border border-primary/20 bg-primary/5 px-4 py-2.5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-medium text-foreground">
                Regulatory Insight Engine v0.1.0-beta
              </span>
              <span className="text-[11px] text-muted-foreground">
                Runtime locale · corpus regolamentare verificabile
              </span>
            </div>
          </div>

          {/* Metrics */}
          <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <MetricCard
              icon={FileStack}
              label="Documenti indicizzati"
              value={indexedDocs.length}
              hint={`su ${apiDocs.length} totali`}
              tone="info"
            />
            <MetricCard
              icon={Layers}
              label="Chunk indicizzati"
              value={totalChunks.toLocaleString()}
              hint={health?.ready ? "indice reale pronto" : `chunk size ${config.chunkSize}`}
            />
            <MetricCard
              icon={Cpu}
              label="Modello attivo"
              value={health?.activeChatModel ?? config.model}
              hint={apiOnline ? "Ollama online" : "API non collegata"}
              tone="success"
            />
            <MetricCard
              icon={Database}
              label="Top-K retrieval"
              value={config.topK}
              hint={health?.embedModel ? `embedding ${health.embedModel}` : `overlap ${config.overlap}`}
            />
          </div>

          {/* Empty state shown above ask box when no answer yet */}
          {!answer && !loading && (
            <div className="mb-5">
              <EmptyState steps={setupSteps} />
            </div>
          )}

          {/* Read-only banner */}
          {readOnly && answer && (
            <div className="mb-3 flex items-center justify-between gap-3 rounded-md border border-primary/20 bg-primary/5 px-3 py-2 text-xs">
              <span className="text-foreground">
                <span className="font-medium">Modalità lettura</span> · stai consultando una voce dello storico.
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 gap-1 text-xs"
                onClick={() => {
                  setReadOnly(false);
                  setAnswer(null);
                  setActiveHistoryId(null);
                }}
              >
                <X className="h-3.5 w-3.5" /> Nuova interrogazione
              </Button>
            </div>
          )}

          {/* Ask */}
          {!readOnly && (
            <div className="mb-5">
              <AskBox onAsk={handleAsk} isLoading={loading} />
            </div>
          )}

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
              docs={apiDocs}
              onImport={() => toast({ title: "Importazione PDF", description: "Aggiungi PDF nella cartella normativa del motore RAG e ricostruisci l'indice." })}
              onDownload={handleRebuild}
              downloadLabel="Ricostruisci indice"
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

        {/* Right history sidebar (desktop) */}
        <div
          className={`hidden shrink-0 border-l border-border bg-card transition-all duration-200 lg:block ${
            historyOpen ? "w-[320px]" : "w-0 overflow-hidden"
          }`}
        >
          {historyOpen && (
            <div className="sticky top-[57px] h-[calc(100vh-57px)]">
              <HistoryPanel
                activeId={activeHistoryId}
                onSelect={(e) => {
                  setAnswer(e.answer);
                  setActiveHistoryId(e.id);
                  setReadOnly(true);
                }}
                onClose={() => setHistoryOpen(false)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Index;
