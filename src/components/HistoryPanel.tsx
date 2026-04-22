import { useMemo, useState } from "react";
import { History, Trash2, X, MessageSquareText, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  HistoryEntry,
  HistoryGroup,
  groupOf,
  useHistoryStore,
} from "@/store/historyStore";

interface HistoryPanelProps {
  activeId: string | null;
  onSelect: (entry: HistoryEntry) => void;
  onClose?: () => void;
}

const GROUP_ORDER: HistoryGroup[] = ["Oggi", "Ieri", "Ultimi 7 giorni", "Più vecchi"];

const formatTime = (ts: number) =>
  new Date(ts).toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });

const formatDate = (ts: number) =>
  new Date(ts).toLocaleDateString("it-IT", { day: "2-digit", month: "short" });

export const HistoryPanel = ({ activeId, onSelect, onClose }: HistoryPanelProps) => {
  const entries = useHistoryStore((s) => s.entries);
  const removeEntry = useHistoryStore((s) => s.removeEntry);
  const clearAll = useHistoryStore((s) => s.clearAll);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const grouped = useMemo(() => {
    const map = new Map<HistoryGroup, HistoryEntry[]>();
    for (const e of entries) {
      const g = groupOf(e.timestamp);
      if (!map.has(g)) map.set(g, []);
      map.get(g)!.push(e);
    }
    return map;
  }, [entries]);

  return (
    <TooltipProvider delayDuration={300}>
      <div className="flex h-full flex-col bg-card">
        <header className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Storico</h3>
            <span className="rounded-full bg-secondary px-2 py-0.5 font-mono text-[10px] text-muted-foreground">
              {entries.length}
            </span>
          </div>
          {onClose && (
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </header>

        <div className="flex-1 overflow-y-auto">
          {entries.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center px-6 py-10 text-center">
              <MessageSquareText className="h-8 w-8 text-muted-foreground/50" />
              <p className="mt-3 text-sm font-medium text-foreground">
                Nessuna interrogazione
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Le tue domande compariranno qui, raggruppate per data.
              </p>
            </div>
          ) : (
            <div className="px-2 py-3">
              {GROUP_ORDER.map((g) => {
                const items = grouped.get(g);
                if (!items || items.length === 0) return null;
                return (
                  <section key={g} className="mb-4 last:mb-0">
                    <div className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      {g}
                    </div>
                    <ul className="space-y-1">
                      {items.map((e) => {
                        const active = e.id === activeId;
                        return (
                          <li key={e.id}>
                            <div
                              className={cn(
                                "group relative rounded-md border border-transparent transition-colors",
                                active
                                  ? "border-primary/30 bg-primary/5"
                                  : "hover:border-border hover:bg-secondary/50",
                              )}
                            >
                              <button
                                onClick={() => onSelect(e)}
                                className="flex w-full flex-col items-start gap-1 px-2.5 py-2 text-left"
                              >
                                <div className="flex w-full items-start gap-1.5">
                                  {active && (
                                    <Check className="mt-0.5 h-3 w-3 shrink-0 text-primary" />
                                  )}
                                  <p className="line-clamp-2 flex-1 pr-6 text-xs leading-snug text-foreground">
                                    {e.question}
                                  </p>
                                </div>
                                <div className="flex w-full items-center justify-between gap-2">
                                  <div className="flex flex-wrap items-center gap-1">
                                    {e.tags.slice(0, 3).map((t) => (
                                      <span
                                        key={t}
                                        className="rounded border border-border bg-secondary px-1.5 py-0.5 font-mono text-[9px] text-muted-foreground"
                                      >
                                        {t}
                                      </span>
                                    ))}
                                  </div>
                                  <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
                                    {groupOf(e.timestamp) === "Oggi" || groupOf(e.timestamp) === "Ieri"
                                      ? formatTime(e.timestamp)
                                      : formatDate(e.timestamp)}
                                  </span>
                                </div>
                              </button>

                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <button
                                    onClick={(ev) => {
                                      ev.stopPropagation();
                                      setConfirmDeleteId(e.id);
                                    }}
                                    className="absolute right-1.5 top-1.5 rounded p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
                                    aria-label="Elimina interrogazione"
                                  >
                                    <Trash2 className="h-3 w-3" />
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent side="left">Elimina</TooltipContent>
                              </Tooltip>
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  </section>
                );
              })}
            </div>
          )}
        </div>

        {entries.length > 0 && (
          <footer className="border-t border-border p-3">
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 w-full gap-1.5 text-xs text-muted-foreground hover:text-destructive"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Cancella tutto lo storico
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Cancellare lo storico?</AlertDialogTitle>
                  <AlertDialogDescription>
                    Verranno rimosse {entries.length} interrogazioni dal tuo storico locale.
                    L'operazione non può essere annullata.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Annulla</AlertDialogCancel>
                  <AlertDialogAction onClick={() => clearAll()}>
                    Cancella tutto
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
            <p className="mt-2 text-center text-[10px] text-muted-foreground">
              Storico locale · TTL 90 giorni
            </p>
          </footer>
        )}

        {/* Single delete confirmation */}
        <AlertDialog open={!!confirmDeleteId} onOpenChange={(o) => !o && setConfirmDeleteId(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Eliminare l'interrogazione?</AlertDialogTitle>
              <AlertDialogDescription>
                L'elemento selezionato verrà rimosso dallo storico locale.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Annulla</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => {
                  if (confirmDeleteId) removeEntry(confirmDeleteId);
                  setConfirmDeleteId(null);
                }}
              >
                Elimina
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </TooltipProvider>
  );
};
