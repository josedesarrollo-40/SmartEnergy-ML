import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string;
  hint?: string;
  icon: LucideIcon;
  accent?: "blue" | "green" | "amber" | "violet";
  className?: string;
}

const accents: Record<NonNullable<StatCardProps["accent"]>, string> = {
  blue: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  green: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  amber: "bg-amber-500/10 text-amber-600 dark:text-amber-500",
  violet: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
};

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  accent = "blue",
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border bg-card p-5 shadow-sm transition-shadow hover:shadow-md",
        className,
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">{label}</span>
        <span
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-lg",
            accents[accent],
          )}
        >
          <Icon className="h-5 w-5" aria-hidden />
        </span>
      </div>
      <p className="mt-3 text-2xl font-bold tracking-tight tabular-nums">{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}
