export const AnswerSkeleton = () => (
  <div className="panel-elevated overflow-hidden">
    <div className="border-b border-border bg-secondary/30 px-5 py-3">
      <div className="flex items-center gap-2">
        <span className="h-2 w-2 animate-pulse rounded-full bg-info" />
        <span className="text-xs font-medium text-muted-foreground">
          Recupero passaggi e generazione risposta…
        </span>
      </div>
    </div>
    <div className="space-y-3 p-5">
      <div className="h-3 w-3/4 animate-pulse rounded bg-secondary" />
      <div className="h-3 w-full animate-pulse rounded bg-secondary" />
      <div className="h-3 w-5/6 animate-pulse rounded bg-secondary" />
      <div className="h-3 w-2/3 animate-pulse rounded bg-secondary" />
      <div className="pt-2">
        <div className="h-3 w-full animate-pulse rounded bg-secondary" />
      </div>
      <div className="h-3 w-4/5 animate-pulse rounded bg-secondary" />
    </div>
  </div>
);
