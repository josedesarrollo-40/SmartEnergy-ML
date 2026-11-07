"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, Coins, Gauge, ListOrdered, TrendingUp, Wallet } from "lucide-react";

import {
  CumulativeChart,
  IntervalChart,
  type CumulativePoint,
  type IntervalPoint,
} from "@/components/charts/consumption-charts";
import { StatCard } from "@/components/stat-card";
import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api";
import { formatCOP, formatDate, formatDateShort, formatKwh } from "@/lib/format";
import type { ReadingOut, SummaryOut } from "@/lib/types";

export default function AnaliticaPage() {
  const [summary, setSummary] = useState<SummaryOut | null>(null);
  const [readings, setReadings] = useState<ReadingOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState({ start: "", end: "" });
  const [applied, setApplied] = useState<{ start: string; end: string } | null>(null);

  const load = useCallback(async (start?: string, end?: string) => {
    setLoading(true);
    setError(null);
    try {
      const [s, r] = await Promise.all([
        api.getSummary(),
        api.listReadingsRange(start, end),
      ]);
      setSummary(s);
      setReadings(r);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error al cargar la analítica.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Intervalos de consumo (diferencia entre lecturas consecutivas del conjunto).
  const intervals: IntervalPoint[] = useMemo(() => {
    const out: IntervalPoint[] = [];
    for (let i = 1; i < readings.length; i++) {
      const prev = readings[i - 1];
      const cur = readings[i];
      if (cur.value_kwh < prev.value_kwh) continue; // incoherente, se omite
      out.push({
        label: `${formatDateShort(prev.reading_date)} → ${formatDateShort(cur.reading_date)}`,
        start: formatDate(prev.reading_date),
        end: formatDate(cur.reading_date),
        kwh: Number((cur.value_kwh - prev.value_kwh).toFixed(3)),
      });
    }
    return out;
  }, [readings]);

  // Lecturas acumuladas (evolución del contador).
  const cumulative: CumulativePoint[] = useMemo(
    () =>
      readings.map((r) => ({
        date: formatDateShort(r.reading_date),
        value: r.value_kwh,
      })),
    [readings],
  );

  function applyFilters(e: React.FormEvent) {
    e.preventDefault();
    if (filters.start && filters.end && filters.start > filters.end) {
      setError("La fecha de inicio no puede ser posterior a la final.");
      return;
    }
    setApplied(filters.start || filters.end ? { ...filters } : null);
    load(filters.start || undefined, filters.end || undefined);
  }

  function clearFilters() {
    setFilters({ start: "", end: "" });
    setApplied(null);
    load();
  }

  const hasData = readings.length > 0;

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Analítica</h1>
        <p className="text-sm text-muted-foreground">
          Consumo e indicadores a partir de las lecturas reales.
        </p>
      </header>

      {/* Indicadores (del resumen global) */}
      {summary ? (
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatCard label="Consumo del periodo" value={formatKwh(summary.total_kwh)} icon={Activity} accent="green" />
          <StatCard label="Promedio diario" value={`${formatKwh(summary.avg_daily_kwh)}/día`} icon={Gauge} accent="blue" />
          <StatCard label="Costo estimado" value={formatCOP(summary.estimated_cost)} icon={Coins} accent="amber" />
          <StatCard label="Lecturas registradas" value={String(readings.length)} icon={ListOrdered} accent="blue" />
          <StatCard
            label="Proyección mensual"
            value={formatKwh(summary.monthly_projection_kwh)}
            hint="Estimación estadística (promedio × 30)"
            icon={TrendingUp}
            accent="violet"
          />
          <StatCard label="Costo proyectado" value={formatCOP(summary.monthly_projection_cost)} icon={Wallet} accent="amber" />
        </div>
      ) : null}

      {/* Filtros */}
      <form onSubmit={applyFilters} className="mb-6 flex flex-wrap items-end gap-3 rounded-xl border bg-card p-4">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium">Desde</span>
          <input
            type="date"
            value={filters.start}
            onChange={(e) => setFilters({ ...filters, start: e.target.value })}
            className="rounded-md border bg-background px-3 py-2"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium">Hasta</span>
          <input
            type="date"
            value={filters.end}
            onChange={(e) => setFilters({ ...filters, end: e.target.value })}
            className="rounded-md border bg-background px-3 py-2"
          />
        </label>
        <Button type="submit">Aplicar filtro</Button>
        {applied ? (
          <Button type="button" variant="ghost" onClick={clearFilters}>
            Limpiar
          </Button>
        ) : null}
      </form>

      {applied ? (
        <div className="mb-4 rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-muted-foreground">
          El consumo del primer intervalo mostrado se calcula a partir de la primera
          lectura dentro del rango; la lectura anterior al rango no se incluye. Un
          endpoint que entregue esa lectura previa permitiría calcular ese primer
          intervalo con exactitud.
        </div>
      ) : null}

      {loading ? (
        <div className="h-72 animate-pulse rounded-xl border bg-muted/40" aria-hidden />
      ) : null}

      {!loading && error ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      {!loading && !error && !hasData ? (
        <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
          No hay lecturas en este rango para graficar.
        </div>
      ) : null}

      {!loading && !error && hasData ? (
        <div className="space-y-8">
          <section className="rounded-xl border bg-card p-5 shadow-sm">
            <h2 className="mb-1 text-lg font-semibold">Consumo por intervalo</h2>
            <p className="mb-4 text-sm text-muted-foreground">
              kWh entre lecturas consecutivas. Cada barra es un intervalo, no un día.
            </p>
            {intervals.length > 0 ? (
              <IntervalChart data={intervals} />
            ) : (
              <p className="py-8 text-center text-sm text-muted-foreground">
                Se necesitan al menos dos lecturas para calcular un intervalo.
              </p>
            )}
          </section>

          <section className="rounded-xl border bg-card p-5 shadow-sm">
            <h2 className="mb-1 text-lg font-semibold">Lecturas acumuladas</h2>
            <p className="mb-4 text-sm text-muted-foreground">
              Evolución del valor del contador en el tiempo.
            </p>
            <CumulativeChart data={cumulative} />
          </section>
        </div>
      ) : null}
    </div>
  );
}
