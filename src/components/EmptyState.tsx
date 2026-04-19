import { ScrollText, ArrowRight, CheckCircle2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

interface SetupStep {
  label: string;
  description: string;
  done: boolean;
}

interface EmptyStateProps {
  steps: SetupStep[];
}

export const EmptyState = ({ steps }: EmptyStateProps) => {
  return (
    <div className="panel-elevated overflow-hidden">
      <div className="grid gap-0 md:grid-cols-[1fr_1.1fr]">
        <div className="border-b border-border bg-gradient-to-br from-primary to-primary-hover p-7 text-primary-foreground md:border-b-0 md:border-r">
          <div className="mb-4 inline-flex h-9 w-9 items-center justify-center rounded-lg bg-white/15 backdrop-blur">
            <ScrollText className="h-5 w-5" />
          </div>
          <h2 className="text-lg font-semibold tracking-tight">
            Pronto a interrogare la normativa.
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-primary-foreground/80">
            Gen.Is.IA fornisce risposte tecniche su IFRS 9, CRR e regolamentazione bancaria,
            sempre fondate su passaggi documentali tracciabili. Nessun dato lascia il perimetro.
          </p>
          <ul className="mt-6 space-y-2.5 text-xs text-primary-foreground/85">
            <li className="flex items-start gap-2">
              <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              Risposte ancorate alle fonti, mai inventate
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              Modelli locali, dati on-premise
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              Esportazione strutturata per audit e revisione
            </li>
          </ul>
        </div>

        <div className="p-7">
          <div className="mb-4 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Configurazione iniziale
          </div>
          <ol className="space-y-3">
            {steps.map((step, i) => (
              <li
                key={step.label}
                className={cn(
                  "flex items-start gap-3 rounded-md border p-3 transition-colors",
                  step.done
                    ? "border-success/20 bg-success/5"
                    : "border-border bg-card hover:border-primary/30"
                )}
              >
                <div className="mt-0.5">
                  {step.done ? (
                    <CheckCircle2 className="h-4 w-4 text-success" />
                  ) : (
                    <Circle className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] text-muted-foreground">
                      0{i + 1}
                    </span>
                    <span className="text-sm font-medium text-foreground">{step.label}</span>
                  </div>
                  <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
                    {step.description}
                  </p>
                </div>
                {!step.done && (
                  <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
                )}
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
};
