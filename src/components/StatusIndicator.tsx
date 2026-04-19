import { cn } from "@/lib/utils";

type Status = "online" | "offline" | "warning" | "loading";

interface StatusIndicatorProps {
  status: Status;
  label: string;
  detail?: string;
  className?: string;
}

const statusStyles: Record<Status, { dot: string; ring: string }> = {
  online: { dot: "bg-success", ring: "bg-success/30" },
  offline: { dot: "bg-muted-foreground", ring: "bg-muted-foreground/20" },
  warning: { dot: "bg-warning", ring: "bg-warning/30" },
  loading: { dot: "bg-info animate-pulse", ring: "bg-info/30 animate-pulse" },
};

export const StatusIndicator = ({ status, label, detail, className }: StatusIndicatorProps) => {
  const styles = statusStyles[status];
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <span className="relative flex h-2.5 w-2.5 items-center justify-center">
        <span className={cn("absolute inline-flex h-full w-full rounded-full opacity-75", styles.ring)} />
        <span className={cn("relative inline-flex h-2 w-2 rounded-full", styles.dot)} />
      </span>
      <div className="flex flex-col leading-tight">
        <span className="text-xs font-medium text-foreground">{label}</span>
        {detail && <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{detail}</span>}
      </div>
    </div>
  );
};
