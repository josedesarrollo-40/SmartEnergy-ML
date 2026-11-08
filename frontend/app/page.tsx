"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  BarChart3,
  CalendarClock,
  Coins,
  Gauge,
  TrendingUp,
  Wallet,
} from "lucide-react";

import { StatCard } from "@/components/stat-card";
import { api, ApiError } from "@/lib/api";
import { formatCOP, formatDate, formatKwh } from "@/lib/format";
import type { DataQualityOut, SummaryOut } from "@/lib/types";

export default function DashboardPage() {
  const [data, setData] = useState<SummaryOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [quality, setQuality] = useState<DataQualityOut | null>(null);

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
    // Calidad de datos (independiente: su error no rompe el dashboard).
    api
      .getDataQuality()
      .then((q) => {
        if (active) setQuality(q);
      })
      .catch(() => {
        if (active) setQuality(null);
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
            accent="blue"
          />
          <StatCard
            label="Consumo del periodo"
            value={formatKwh(data.total_kwh)}
            icon={Activity}
            accent="green"
          />
          <StatCard
            label="Promedio diario"
            value={`${formatKwh(data.avg_daily_kwh)}/día`}
            icon={Gauge}
            accent="blue"
          />
          <StatCard
            label="Costo estimado"
            value={formatCOP(data.estimated_cost)}
            icon={Coins}
            accent="amber"
          />
          <StatCard
            label="Proyección mensual"
            value={formatKwh(data.monthly_projection_kwh)}
            hint="Estimación estadística (promedio × 30)"
            icon={TrendingUp}
            accent="violet"
          />
          <StatCard
            label="Costo proyectado"
            value={formatCOP(data.monthly_projection_cost)}
            icon={Wallet}
            accent="amber"
          />
        </div>
      ) : null}

      {/* Calidad de datos */}
      {quality ? <DataQualitySection q={quality} /> : null}

      {/* Comportamiento del consumo: enlaza a la sección de gráficas. */}
      {!loading && !error && data && hasReadings ? (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold">Comportamiento del consumo</h2>
          <div className="rounded-xl border bg-card p-6 shadow-sm">
            <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-start gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                  <BarChart3 className="h-5 w-5" aria-hidden />
                </span>
                <div>
                  <p className="font-medium">Consultar gráficas detalladas</p>
                  <p className="text-sm text-muted-foreground">
                    Consumo por intervalo y evolución del contador en el tiempo.
                  </p>
                </div>
              </div>
              <Link
                href="/analitica"
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:opacity-90"
              >
                Ver analítica
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </div>
          </div>
        </section>
      ) : null}
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

function QualityStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border bg-background p-3 text-center">
      <p className="text-xl font-bold tabular-nums">{value}</p>
      <p className="mt-0.5 text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

function DataQualitySection({ q }: { q: DataQualityOut }) {
  const c = q.confidence_counts ?? {};
  return (
    <section className="mt-8">
      <h2 className="mb-1 text-lg font-semibold">Calidad de datos</h2>
      <p className="mb-4 text-sm text-muted-foreground">
        Cuánta de la información es medición real y cuánta es estimada. Los días
        interpolados y las lecturas pendientes no son mediciones confirmadas.
      </p>
      <div className="rounded-xl border bg-card p-5 shadow-sm">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <QualityStat label="Lecturas" value={q.total_readings} />
          <QualityStat label="Días observados" value={q.observed_days} />
          <QualityStat label="Días interpolados" value={q.interpolated_days} />
          <QualityStat label="Con hora real" value={q.time_known_count} />
          <QualityStat label="Intervalos irregulares" value={q.irregular_intervals.length} />
          <QualityStat label="Verificadas" value={c.verified ?? 0} />
          <QualityStat label="Confirmadas" value={c.confirmed ?? 0} />
          <QualityStat label="Inferidas" value={c.inferred ?? 0} />
          <QualityStat label="Pendientes" value={c.pending ?? 0} />
        </div>
        <div className="mt-4 space-y-1 text-xs text-muted-foreground">
          <p>
            <strong>Interpolado:</strong> día sin lectura propia; su consumo se
            reparte desde una lectura posterior. No es una medición directa.
          </p>
          <p>
            <strong>Pendiente / inferida:</strong> la fecha aún no está
            confirmada. Úsalas con cautela para análisis.
          </p>
        </div>
      </div>
    </section>
  );
}
