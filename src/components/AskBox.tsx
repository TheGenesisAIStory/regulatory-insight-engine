import { useState, KeyboardEvent } from "react";
import { Send, Sparkles, CornerDownLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface AskBoxProps {
  onAsk: (q: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

const SUGGESTIONS = [
  "Quali sono i criteri per il passaggio dallo Stage 1 allo Stage 2 secondo IFRS 9?",
  "Definizione di esposizione in default ai sensi del CRR art. 178",
  "Calcolo dell'ECL lifetime su esposizioni POCI",
  "Requisiti sulla concentrazione dei rischi nel CRR",
];

export const AskBox = ({ onAsk, isLoading, disabled }: AskBoxProps) => {
  const [value, setValue] = useState("");

  const submit = () => {
    const q = value.trim();
    if (!q || isLoading || disabled) return;
    onAsk(q);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="panel-elevated overflow-hidden">
      <div className="border-b border-border bg-secondary/30 px-4 py-2.5">
        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <Sparkles className="h-3.5 w-3.5" />
          Nuova interrogazione normativa
        </div>
      </div>
      <div className="p-4">
        <Textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Es. Secondo IFRS 9, quando un'esposizione passa allo Stage 2 e quali fonti supportano la risposta?"
          disabled={disabled || isLoading}
          rows={3}
          className="resize-none border-0 p-0 text-base shadow-none focus-visible:ring-0"
        />

        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <CornerDownLeft className="h-3 w-3" />
            <span>
              <kbd className="rounded border border-border bg-secondary px-1 py-0.5 font-mono text-[10px]">⌘</kbd>{" "}
              <kbd className="rounded border border-border bg-secondary px-1 py-0.5 font-mono text-[10px]">Enter</kbd>{" "}
              per inviare
            </span>
          </div>
          <Button
            onClick={submit}
            disabled={!value.trim() || isLoading || disabled}
            size="sm"
            className="gap-2"
          >
            {isLoading ? (
              <>
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
                Analisi in corso…
              </>
            ) : (
              <>
                <Send className="h-3.5 w-3.5" />
                Interroga
              </>
            )}
          </Button>
        </div>
      </div>

      {!disabled && (
        <div className="border-t border-border bg-secondary/20 px-4 py-3">
          <div className="mb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Domande di esempio
          </div>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => setValue(s)}
                disabled={isLoading}
                className="rounded-md border border-border bg-card px-2.5 py-1.5 text-left text-xs text-muted-foreground transition-colors hover:border-primary/30 hover:bg-secondary hover:text-foreground disabled:opacity-50"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
