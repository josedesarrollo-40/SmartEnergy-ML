"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  CalendarClock,
  Coins,
  Gauge,
  TrendingUp,
  Wallet,
} from "lucide-react";

import { StatCard } from "@/components/stat-card";
import { api, ApiError } from "@/lib/api";
import { formatCOP, formatDate, formatKwh } from "@/lib/format";
import type { SummaryOut } from "@/lib/types";

export default function DashboardPage() {
  const [data, setData] = useState<SummaryOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    api
      .getSummary()
      .then((d) => {
        if (active) setData(d);
      })
      .catch((e) => {
        if (active) setError(e instanceof ApiError ? e.message : "Error inesperado.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const hasReadings = data?.last_reading_date != null;

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Resumen del consumo eléctrico de la vivienda.
        </p>
      </header>

      {loading ? <LoadingGrid /> : null}

      {!loading && error ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm">
          <p className="font-medium text-destructive">No se pudo cargar el resumen</p>
          <p className="mt-1 text-muted-foreground">{error}</p>
        </div>
      ) : null}

      {!loading && !error && data && !hasReadings ? (
        <div className="rounded-lg border bg-card p-8 text-center">
          <Gauge className="mx-auto h-8 w-8 text-muted-foreground" aria-hidden />
          <p className="mt-3 font-medium">Aún no hay lecturas registradas</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Registra tu primera lectura del contador para ver el consumo y el costo.
          </p>
        </div>
      ) : null}

      {!loading && !error && data && hasReadings ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatCard
            label="Última lectura"
            value={formatDate(data.last_reading_date)}
            hint={
              data.last_reading_value != null
                ? `${formatKwh(data.last_reading_value)} en el contador`
                : undefined
            }
            icon={CalendarClock}
          />
          <StatCard
            label="Consumo del periodo"
            value={formatKwh(data.total_kwh)}
            icon={Activity}
          />
          <StatCard
            label="Promedio diario"
            value={`${formatKwh(data.avg_daily_kwh)}/día`}
            icon={Gauge}
          />
          <StatCard
            label="Costo estimado"
            value={formatCOP(data.estimated_cost)}
            icon={Coins}
          />
          <StatCard
            label="Proyección mensual"
            value={formatKwh(data.monthly_projection_kwh)}
            hint="Estimación estadística (promedio × 30), no ML"
            icon={TrendingUp}
          />
          <StatCard
            label="Costo proyectado"
            value={formatCOP(data.monthly_projection_cost)}
            icon={Wallet}
          />
        </div>
      ) : null}

      {/* Sección de gráficas: pendiente de un endpoint histórico en el backend. */}
      <section className="mt-8">
        <h2 className="mb-3 text-lg font-semibold">Comportamiento del consumo</h2>
        <div className="rounded-lg border border-dashed bg-card p-8 text-center text-sm text-muted-foreground">
          La gráfica histórica estará disponible cuando el backend exponga un
          endpoint de serie temporal (por ejemplo{" "}
          <code className="rounded bg-muted px-1 py-0.5">/api/analytics/history</code>
          ). Hoy el backend solo ofrece el resumen agregado.
        </div>
      </section>
    </div>
  );
}

function LoadingGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="h-28 animate-pulse rounded-xl border bg-muted/40"
          aria-hidden
        />
      ))}
    </div>
  );
}
