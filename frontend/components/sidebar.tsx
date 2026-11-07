"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Gauge, LayoutDashboard, Zap } from "lucide-react";

import { cn } from "@/lib/utils";

const items = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/lecturas", label: "Lecturas", icon: Gauge },
  { href: "/tarifas", label: "Tarifas", icon: Zap },
  { href: "/analitica", label: "Analítica", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-full shrink-0 flex-col border-b bg-card md:h-screen md:w-64 md:border-b-0 md:border-r">
      <div className="flex items-center gap-2 px-6 py-5">
        <Zap className="h-6 w-6 text-yellow-500" aria-hidden />
        <span className="text-lg font-semibold">SmartEnergy ML</span>
      </div>
      <nav className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:overflow-visible">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
              )}
            >
              <Icon className="h-4 w-4" aria-hidden />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
