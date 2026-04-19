import { Cpu, Settings2, Zap, Database, Layers, Sliders } from "lucide-react";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";

export interface AssistantConfig {
  model: string;
  topK: number;
  chunkSize: number;
  overlap: number;
  fastMode: boolean;
}

interface ConfigSidebarProps {
  config: AssistantConfig;
  onChange: (config: AssistantConfig) => void;
  onRebuildIndex: () => void;
}

export const ConfigSidebar = ({ config, onChange, onRebuildIndex }: ConfigSidebarProps) => {
  const update = <K extends keyof AssistantConfig>(key: K, value: AssistantConfig[K]) =>
    onChange({ ...config, [key]: value });

  return (
    <aside className="flex h-full w-full flex-col gap-5 overflow-y-auto scrollbar-thin p-5 lg:p-6">
      <div>
        <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <Settings2 className="h-3.5 w-3.5" />
          Configurazione
        </div>
        <p className="text-xs text-muted-foreground/80">
          Parametri di recupero e generazione utilizzati per ogni richiesta.
        </p>
      </div>

      {/* Model */}
      <section className="space-y-2.5">
        <Label className="flex items-center gap-2 text-xs font-medium">
          <Cpu className="h-3.5 w-3.5 text-muted-foreground" /> Modello locale
        </Label>
        <Select value={config.model} onValueChange={(v) => update("model", v)}>
          <SelectTrigger className="h-9 text-sm">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="qwen2.5:3b">qwen2.5:3b · originale</SelectItem>
            <SelectItem value="llama3.1:latest">llama3.1 · locale</SelectItem>
            <SelectItem value="llama3.1:8b">llama3.1:8b · generale</SelectItem>
            <SelectItem value="mistral:7b">mistral:7b · veloce</SelectItem>
            <SelectItem value="qwen2.5:14b">qwen2.5:14b · accurato</SelectItem>
            <SelectItem value="phi3:mini">phi3:mini · leggero</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-[11px] text-muted-foreground">
          Servito tramite runtime locale. Nessuna chiamata esterna.
        </p>
      </section>

      <div className="h-px bg-border" />

      {/* Fast mode */}
      <section className="flex items-start justify-between gap-3">
        <div className="space-y-0.5">
          <Label htmlFor="fast-mode" className="flex items-center gap-2 text-xs font-medium">
            <Zap className="h-3.5 w-3.5 text-muted-foreground" /> Modalità rapida
          </Label>
          <p className="text-[11px] text-muted-foreground">
            Riduce contesto e temperatura per risposte più brevi.
          </p>
        </div>
        <Switch
          id="fast-mode"
          checked={config.fastMode}
          onCheckedChange={(v) => update("fastMode", v)}
        />
      </section>

      <div className="h-px bg-border" />

      {/* Top-K */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="flex items-center gap-2 text-xs font-medium">
            <Layers className="h-3.5 w-3.5 text-muted-foreground" /> Top-K passaggi
          </Label>
          <span className="font-mono text-xs text-foreground">{config.topK}</span>
        </div>
        <Slider
          value={[config.topK]}
          min={2}
          max={12}
          step={1}
          onValueChange={([v]) => update("topK", v)}
        />
        <p className="text-[11px] text-muted-foreground">
          Numero di estratti recuperati per ogni domanda.
        </p>
      </section>

      {/* Chunk size */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="flex items-center gap-2 text-xs font-medium">
            <Sliders className="h-3.5 w-3.5 text-muted-foreground" /> Dimensione chunk
          </Label>
          <span className="font-mono text-xs text-foreground">{config.chunkSize}</span>
        </div>
        <Slider
          value={[config.chunkSize]}
          min={256}
          max={2048}
          step={64}
          onValueChange={([v]) => update("chunkSize", v)}
        />
      </section>

      {/* Overlap */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-xs font-medium">Overlap</Label>
          <span className="font-mono text-xs text-foreground">{config.overlap}</span>
        </div>
        <Slider
          value={[config.overlap]}
          min={0}
          max={400}
          step={20}
          onValueChange={([v]) => update("overlap", v)}
        />
        <p className="text-[11px] text-muted-foreground">
          Sovrapposizione tra chunk per preservare il contesto.
        </p>
      </section>

      <div className="h-px bg-border" />

      <section className="space-y-2">
        <Label className="flex items-center gap-2 text-xs font-medium">
          <Database className="h-3.5 w-3.5 text-muted-foreground" /> Indice vettoriale
        </Label>
        <Button
          variant="outline"
          size="sm"
          onClick={onRebuildIndex}
          className="w-full justify-center text-xs"
        >
          Ricostruisci indice
        </Button>
        <p className="text-[11px] text-muted-foreground">
          Riprocessa i documenti dopo modifiche o nuovi caricamenti.
        </p>
      </section>

      <div className="mt-auto rounded-md border border-border bg-secondary/40 p-3">
        <p className="text-[11px] leading-relaxed text-muted-foreground">
          Le modifiche ai parametri sono applicate alle prossime interrogazioni.
          Le risposte sono <span className="font-medium text-foreground">sempre tracciabili</span> alle fonti recuperate.
        </p>
      </div>
    </aside>
  );
};
