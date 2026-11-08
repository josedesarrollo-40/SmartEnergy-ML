"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Gauge, LayoutDashboard, Zap } from "lucide-react";

import { LogoMark } from "@/components/logo";
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
    <aside className="flex w-full shrink-0 flex-col bg-sidebar text-sidebar-foreground md:h-screen md:w-64">
      <div className="flex items-center gap-2.5 px-6 py-6">
        <LogoMark className="h-9 w-9" />
        <div className="leading-tight">
          <span className="block text-base font-semibold">SmartEnergy ML</span>
          <span className="block text-xs text-sidebar-foreground/60">
            Análisis energético
          </span>
        </div>
      </div>
      <nav className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:overflow-visible">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-sidebar-primary text-sidebar-primary-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
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
