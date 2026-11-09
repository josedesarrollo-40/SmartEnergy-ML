"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  CloudSun,
  Coins,
  Gauge,
  ListOrdered,
  Loader2,
  RefreshCw,
  TrendingUp,
  Wallet,
} from "lucide-react";

import {
  CumulativeChart,
  IntervalChart,
  WeatherConsumptionChart,
  type CumulativePoint,
  type IntervalPoint,
  type WeatherConsumptionPoint,
} from "@/components/charts/consumption-charts";
import { StatCard } from "@/components/stat-card";
import { Button } from "@/components/ui/button";
import { LoadingOverlay } from "@/components/ui/loading-overlay";
import { PaginationBar, usePagination } from "@/components/ui/pagination";
import { api, ApiError } from "@/lib/api";
import {
  formatCOP,
  formatDate,
  formatDateShort,
  formatKwh,
  monthLabelFrom,
} from "@/lib/format";
import type {
  IntervalWeatherRow,
  PeriodConsumptionOut,
  ReadingOut,
  SummaryOut,
} from "@/lib/types";

export default function AnaliticaPage() {
  const [summary, setSummary] = useState<SummaryOut | null>(null);
  const [readings, setReadings] = useState<ReadingOut[]>([]);
  const [monthToDate, setMonthToDate] = useState<PeriodConsumptionOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const [filters, setFilters] = useState({ start: "", end: "" });
  const [applied, setApplied] = useState<{ start: string; end: string } | null>(null);
  // Consumo/costo del rango filtrado: lo calcula el backend con tarifa
  // histórica. Solo se consulta cuando hay un rango completo (start y end).
  const [period, setPeriod] = useState<PeriodConsumptionOut | null>(null);

  const load = useCallback(async (start?: string, end?: string) => {
    setLoading(true);
    setError(null);
    try {
      const [s, r, m] = await Promise.all([
        api.getSummary(),
        api.listReadingsRange(start, end),
        api.getCurrentMonthToDate().catch(() => null),
      ]);
      setSummary(s);
      setReadings(r);
      setMonthToDate(m);
      // El costo del rango lo entrega el backend (respeta la tarifa vigente en
      // cada tramo). Requiere ambos extremos del rango.
      if (start && end) {
        try {
          setPeriod(await api.getPeriod(start, end));
        } catch {
          setPeriod(null);
        }
      } else {
        setPeriod(null);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error al cargar la analítica.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, reloadKey]);

  const periodKwh =
    monthToDate && monthToDate.sufficient ? monthToDate.kwh : summary?.total_kwh ?? 0;
  const periodHint =
    monthToDate && monthToDate.sufficient
      ? `Del 1 de ${monthLabelFrom(monthToDate.start)} a hoy`
      : "Acumulado del mes en curso";

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
      <LoadingOverlay
        open={loading && !summary}
        message="Cargando la analítica…"
        error={!loading && error && !summary ? error : null}
        onRetry={() => setReloadKey((k) => k + 1)}
      />

      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Analítica</h1>
        <p className="text-sm text-muted-foreground">
          Consumo e indicadores a partir de las lecturas reales.
        </p>
      </header>

      {/* Indicadores (del resumen global) */}
      {summary ? (
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatCard label="Consumo del periodo" value={formatKwh(periodKwh)} hint={periodHint} icon={Activity} accent="green" />
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

      {/* Costo del rango filtrado, calculado por el backend con tarifa histórica. */}
      {applied && period ? (
        <div className="mb-4 rounded-xl border bg-card p-5 shadow-sm">
          <h2 className="mb-1 text-lg font-semibold">
            Costo del rango seleccionado
          </h2>
          <p className="mb-4 text-sm text-muted-foreground">
            {formatDate(period.start)} – {formatDate(period.end)}. Cada tramo se
            cobra con la tarifa vigente en su fecha (cálculo del backend).
          </p>
          {period.sufficient ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border p-3">
                <p className="text-xs text-muted-foreground">Consumo</p>
                <p className="text-xl font-bold tabular-nums">
                  {formatKwh(period.kwh)}
                </p>
              </div>
              <div className="rounded-lg border p-3">
                <p className="text-xs text-muted-foreground">Costo estimado</p>
                <p className="text-xl font-bold tabular-nums">
                  {formatCOP(period.estimated_cost)}
                </p>
              </div>
            </div>
          ) : (
            <p className="rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-muted-foreground">
              Información insuficiente para calcular este rango con las lecturas
              disponibles.
            </p>
          )}
          {period.sufficient && period.estimated ? (
            <p className="mt-3 text-xs text-amber-600 dark:text-amber-500">
              Incluye interpolación en los bordes:{" "}
              {Math.round(period.estimated_fraction * 100)}% del consumo es estimado.
            </p>
          ) : null}
        </div>
      ) : null}

      {applied ? (
        <div className="mb-4 rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-muted-foreground">
          El consumo del primer intervalo mostrado en las gráficas se calcula a partir
          de la primera lectura dentro del rango; la lectura anterior al rango no se
          incluye. El costo del rango (arriba) sí lo entrega el backend con las
          tarifas históricas correctas.
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

      <WeatherSection />
    </div>
  );
}

const WEATHER_STATUS: Record<string, { label: string; style: string }> = {
  available: {
    label: "Disponible",
    style: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400",
  },
  pending: {
    label: "Pendiente",
    style: "bg-amber-500/15 text-amber-700 dark:text-amber-500",
  },
  failed: {
    label: "Fallido",
    style: "bg-red-500/15 text-red-700 dark:text-red-400",
  },
  unavailable: {
    label: "No disponible",
    style: "bg-muted text-muted-foreground",
  },
};

function WeatherStatusBadge({ value }: { value: string }) {
  const s = WEATHER_STATUS[value] ?? WEATHER_STATUS.unavailable;
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${s.style}`}>
      {s.label}
    </span>
  );
}

function fmtTemp(v: number | null): string {
  return v === null ? "—" : `${v.toFixed(1)} °C`;
}

function fmtHum(v: number | null): string {
  return v === null ? "—" : `${v.toFixed(0)} %`;
}

// Variables climáticas por intervalo (Open-Meteo). Los datos vienen del backend;
// aquí solo se presentan, distinguiendo disponibles de pendientes/fallidos.
function WeatherSection() {
  const [rows, setRows] = useState<IntervalWeatherRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recovering, setRecovering] = useState(false);
  const [recoverMsg, setRecoverMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRows(await api.listIntervalWeather());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error al cargar el clima.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Solo LECTURA al montar: no dispara llamadas a Open-Meteo.
  useEffect(() => {
    load();
  }, [load]);

  async function onRecover() {
    setRecovering(true);
    setRecoverMsg(null);
    try {
      const r = await api.recoverWeather();
      setRecoverMsg(
        `Revisados ${r.checked} · actualizados ${r.updated} · ` +
          `pendientes ${r.still_pending} · fallidos ${r.failed}.`,
      );
      await load();
    } catch (e) {
      setRecoverMsg(
        e instanceof ApiError ? e.message : "No se pudo recuperar el clima.",
      );
    } finally {
      setRecovering(false);
    }
  }

  // Serie para la gráfica temp vs consumo (orden cronológico ascendente).
  const chart: WeatherConsumptionPoint[] = useMemo(
    () =>
      rows.map((w) => ({
        label: `${formatDateShort(w.start_date)} → ${formatDateShort(w.end_date)}`,
        kwh: w.consumption_kwh,
        temp: w.temp_avg_c,
      })),
    [rows],
  );

  const pendingCount = rows.filter(
    (w) => w.status === "pending" || w.status === "failed",
  ).length;
  const hasAnyWeather = rows.some((w) => w.temp_avg_c !== null);

  // Paginación de la tabla de intervalos (10 por página, como Lecturas).
  const pager = usePagination(rows, 10, rows.length);

  return (
    <section className="mt-8">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-500/10 text-sky-600 dark:text-sky-400">
            <CloudSun className="h-5 w-5" aria-hidden />
          </span>
          <div>
            <h2 className="text-lg font-semibold">Clima por intervalo</h2>
            <p className="text-sm text-muted-foreground">
              Temperatura y humedad del periodo entre lecturas, frente al consumo.
            </p>
          </div>
        </div>
        {pendingCount > 0 ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onRecover}
            disabled={recovering}
          >
            {recovering ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <RefreshCw className="h-4 w-4" aria-hidden />
            )}
            Recuperar pendientes ({pendingCount})
          </Button>
        ) : null}
      </div>

      {recoverMsg ? (
        <p className="mb-3 text-xs text-muted-foreground">{recoverMsg}</p>
      ) : null}

      {loading ? (
        <div className="h-48 animate-pulse rounded-xl border bg-muted/40" aria-hidden />
      ) : null}

      {!loading && error ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      {!loading && !error && rows.length === 0 ? (
        <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
          Se necesitan al menos dos lecturas para formar un intervalo con clima.
        </div>
      ) : null}

      {!loading && !error && rows.length > 0 ? (
        <div className="space-y-6">
          {hasAnyWeather ? (
            <div className="rounded-xl border bg-card p-5 shadow-sm">
              <h3 className="mb-1 text-base font-semibold">
                Temperatura vs consumo
              </h3>
              <p className="mb-4 text-sm text-muted-foreground">
                Barras: consumo del intervalo (kWh). Línea: temperatura promedio
                (°C). Los intervalos sin datos climáticos no trazan línea.
              </p>
              <WeatherConsumptionChart data={chart} />
            </div>
          ) : (
            <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-muted-foreground">
              Todavía no hay datos climáticos disponibles para estos intervalos.
              Usa &quot;Recuperar pendientes&quot; para consultarlos.
            </div>
          )}

          <div className="overflow-x-auto rounded-lg border bg-card">
            <table className="w-full min-w-[640px] text-sm">
              <thead className="border-b text-left text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium whitespace-nowrap">Intervalo</th>
                  <th className="px-4 py-3 font-medium whitespace-nowrap">Consumo</th>
                  <th className="px-4 py-3 font-medium whitespace-nowrap">Temp. prom.</th>
                  <th className="px-4 py-3 font-medium whitespace-nowrap">Máx / mín</th>
                  <th className="px-4 py-3 font-medium whitespace-nowrap">Humedad</th>
                  <th className="px-4 py-3 font-medium whitespace-nowrap">Estado</th>
                </tr>
              </thead>
              <tbody>
                {pager.rows.map((w) => (
                  <tr
                    key={`${w.start_reading_id}-${w.end_reading_id}`}
                    className="border-b last:border-0"
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      {formatDate(w.start_date)} – {formatDate(w.end_date)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {w.consumption_kwh === null
                        ? "—"
                        : formatKwh(w.consumption_kwh)}
                    </td>
                    <td className="px-4 py-3 tabular-nums">{fmtTemp(w.temp_avg_c)}</td>
                    <td className="px-4 py-3 tabular-nums text-muted-foreground">
                      {fmtTemp(w.temp_max_c)} / {fmtTemp(w.temp_min_c)}
                    </td>
                    <td className="px-4 py-3 tabular-nums">{fmtHum(w.humidity_avg_pct)}</td>
                    <td className="px-4 py-3">
                      <WeatherStatusBadge value={w.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {rows.length > 10 ? (
            <PaginationBar
              page={pager.page}
              totalPages={pager.totalPages}
              total={pager.total}
              onPrev={pager.goPrev}
              onNext={pager.goNext}
              unit={["intervalo", "intervalos"]}
            />
          ) : null}
        </div>
      ) : null}

      <p className="mt-3 text-xs text-muted-foreground">
        Fuente: datos meteorológicos de{" "}
        <a
          href="https://open-meteo.com"
          target="_blank"
          rel="noreferrer"
          className="underline hover:text-foreground"
        >
          Open-Meteo.com
        </a>{" "}
        (CC BY 4.0). Ubicación configurada: Ibagué, Tolima.
      </p>
    </section>
  );
}
