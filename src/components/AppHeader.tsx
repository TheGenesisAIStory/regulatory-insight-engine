import { ShieldCheck, Wifi, WifiOff } from "lucide-react";
import { StatusIndicator } from "./StatusIndicator";

interface AppHeaderProps {
  modelStatus: "online" | "offline" | "loading";
  indexStatus: "online" | "warning" | "offline";
}

export const AppHeader = ({ modelStatus, indexStatus }: AppHeaderProps) => {
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-card/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-[1600px] items-center justify-between px-4 py-3 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ShieldCheck className="h-5 w-5" strokeWidth={2.25} />
          </div>
          <div className="flex flex-col leading-tight">
            <h1 className="text-base font-semibold tracking-tight text-foreground">
              Gen.Is.IA
            </h1>
            <p className="hidden text-xs text-muted-foreground sm:block">
              Assistente normativo bancario · IFRS 9 · CRR · Basel
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 sm:gap-5">
          <div className="hidden items-center gap-1.5 rounded-md border border-border bg-secondary/60 px-2.5 py-1.5 md:flex">
            <WifiOff className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              Offline-first
            </span>
          </div>
          <StatusIndicator
            status={modelStatus}
            label={modelStatus === "online" ? "Modello attivo" : "Modello offline"}
            detail="LLM locale"
          />
          <div className="hidden h-8 w-px bg-border sm:block" />
          <StatusIndicator
            status={indexStatus === "online" ? "online" : indexStatus === "warning" ? "warning" : "offline"}
            label={indexStatus === "online" ? "Indice pronto" : "Indice incompleto"}
            detail="Knowledge base"
          />
        </div>
      </div>
    </header>
  );
};
