import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "success" | "warning" | "info";
}

const toneStyles = {
  default: "text-foreground bg-secondary/60 border-border",
  success: "text-success bg-success/10 border-success/20",
  warning: "text-warning bg-warning/10 border-warning/25",
  info: "text-accent bg-accent/10 border-accent/20",
};

export const MetricCard = ({ icon: Icon, label, value, hint, tone = "default" }: MetricCardProps) => {
  return (
    <div className="panel flex items-start gap-3 p-4">
      <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-md border", toneStyles[tone])}>
        <Icon className="h-4 w-4" strokeWidth={2.25} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </div>
        <div className="mt-0.5 truncate font-mono text-lg font-semibold leading-tight text-foreground">
          {value}
        </div>
        {hint && <div className="mt-0.5 truncate text-[11px] text-muted-foreground">{hint}</div>}
      </div>
    </div>
  );
};
