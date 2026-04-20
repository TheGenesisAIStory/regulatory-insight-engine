import { useEffect, useState } from "react";
import { FileStack, Layers, Cpu, Database, PanelLeftClose, PanelLeft } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { ConfigSidebar, AssistantConfig } from "@/components/ConfigSidebar";
import { MetricCard } from "@/components/MetricCard";
import { AskBox } from "@/components/AskBox";
import { AnswerPanel, AnswerData } from "@/components/AnswerPanel";
import { AnswerSkeleton } from "@/components/AnswerSkeleton";
import { EmptyState } from "@/components/EmptyState";
import { MockAnswerCard } from "@/components/MockAnswerCard";
import { DocumentLibrary } from "@/components/DocumentLibrary";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { mockDocs } from "@/data/mockData";
import { toast } from "@/hooks/use-toast";
import { API_BASE_URL, askGenisia, GenisiaApiError, getDocuments, getReadiness, HealthResponse, rebuildIndex } from "@/lib/genisiaApi";

const DEMO_CONVERSATION = {
  question: "Quali sono i requisiti di capitale CRR per il rischio di credito?",
  answer:
    "Secondo l'art. 92 CRR, gli enti devono mantenere un CET1 ≥ 4,5% del Total Risk Exposure Amount. Tier 1 ≥ 6%, Total Capital ≥ 8%.",
  sources: [
    "CRR Art. 92 — Requisiti di fondi propri",
    "EBA SREP Guidelines 2023",
  ],
  score: "Score: 0.87",
  tag: "⚡ Offline — Ollama/mistral",
};

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
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [apiDocs, setApiDocs] = useState(mockDocs);
  const [apiChecked, setApiChecked] = useState(false);
  const [readinessReasons, setReadinessReasons] = useState<string[]>([]);
  const [demoConversation, setDemoConversation] = useState(DEMO_CONVERSATION);

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
    setDemoConversation(null);

    try {
      const data = await askGenisia(q, config.topK, config.model);
      setAnswer(data);
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
      {/* DEMO ONLY — remove before production */}
      <div style={{ background: "#1a1a2e", color: "white", fontSize: "12px", padding: "8px 16px" }}>
        Regulatory Insight Engine v0.1.0-beta — Offline RAG for Banking Compliance
      </div>
      <AppHeader
        modelStatus={!apiChecked ? "loading" : apiOnline ? "online" : "offline"}
        indexStatus={!apiChecked ? "warning" : health?.ready ? "online" : usingRealDocs ? "warning" : "offline"}
      />

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

          {/* Ask */}
          <div className="mb-5">
            {/* DEMO ONLY — remove before production */}
            <AskBox onAsk={handleAsk} isLoading={loading} initialValue={DEMO_CONVERSATION.question} />
          </div>

          {/* DEMO ONLY — remove before production */}
          {demoConversation && !answer && !loading && (
            <div className="mb-5 space-y-3">
              <div className="flex justify-end">
                <div className="max-w-2xl rounded-md border border-primary/20 bg-primary/10 px-4 py-3 text-sm font-medium text-foreground">
                  {demoConversation.question}
                </div>
              </div>

              <article className="panel-elevated overflow-hidden">
                <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-secondary/30 px-5 py-3">
                  <div>
                    <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                      Risposta demo
                    </div>
                    <h3 className="text-sm font-semibold text-foreground">Requisiti di capitale CRR</h3>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full border border-success/25 bg-success/10 px-2.5 py-1 text-[11px] font-medium text-success">
                      {demoConversation.score}
                    </span>
                    <span className="rounded-full border border-border bg-card px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                      {demoConversation.tag}
                    </span>
                  </div>
                </header>
                <div className="space-y-4 px-5 py-5">
                  <p className="text-sm leading-relaxed text-foreground">{demoConversation.answer}</p>
                  <div className="flex flex-wrap gap-2">
                    {demoConversation.sources.map((source) => (
                      <span
                        key={source}
                        className="rounded-full border border-primary/20 bg-primary/5 px-2.5 py-1 text-[11px] font-medium text-primary"
                      >
                        {source}
                      </span>
                    ))}
                  </div>
                </div>
              </article>
            </div>
          )}

          {!demoConversation && !answer && !loading && (
            <div className="mb-5">
              <MockAnswerCard />
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
      </div>
    </div>
  );
};

export default Index;
