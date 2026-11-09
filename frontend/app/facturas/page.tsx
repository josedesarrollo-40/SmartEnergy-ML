"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { LoadingOverlay } from "@/components/ui/loading-overlay";
import { PaginationBar, usePagination } from "@/components/ui/pagination";
import { api, ApiError, type InvoiceCreate } from "@/lib/api";
import { formatCOP, formatDate, formatKwh } from "@/lib/format";
import type { InvoiceComparisonOut, InvoiceOut, PeriodConsumptionOut } from "@/lib/types";

const MONTHS = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

export default function FacturasPage() {
  const [invoices, setInvoices] = useState<InvoiceOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const [form, setForm] = useState({
    period_start: "",
    period_end: "",
    billed_kwh: "",
    billed_amount: "",
    issued_date: "",
    notes: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const [comparison, setComparison] = useState<InvoiceComparisonOut | null>(null);
  const [comparingId, setComparingId] = useState<number | null>(null);

  // Orden estable: período más reciente primero. Se conserva al paginar.
  const sorted = useMemo(
    () =>
      [...invoices].sort((a, b) => b.period_start.localeCompare(a.period_start)),
    [invoices],
  );
  const pager = usePagination(sorted, 10, sorted.length);

  const load = useCallback(async () => {
    setLoading(true);
    setListError(null);
    try {
      setInvoices(await api.listInvoices());
    } catch (e) {
      setListError(e instanceof ApiError ? e.message : "Error al cargar facturas.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSuccess(null);

    const kwh = Number(form.billed_kwh);
    const amount = Number(form.billed_amount);
    if (!form.period_start || !form.period_end) {
      return setFormError("Indica el período (fecha inicial y final).");
    }
    if (form.period_end < form.period_start) {
      return setFormError("La fecha final no puede ser anterior a la inicial.");
    }
    if (form.billed_kwh === "" || Number.isNaN(kwh) || kwh < 0) {
      return setFormError("Indica un consumo facturado válido (kWh ≥ 0).");
    }
    if (form.billed_amount === "" || Number.isNaN(amount) || amount < 0) {
      return setFormError("Indica un valor facturado válido (COP ≥ 0).");
    }

    const payload: InvoiceCreate = {
      period_start: form.period_start,
      period_end: form.period_end,
      billed_kwh: kwh,
      billed_amount: amount,
      issued_date: form.issued_date || null,
      notes: form.notes.trim() || null,
    };

    setSubmitting(true);
    try {
      await api.createInvoice(payload);
      setSuccess("Factura registrada.");
      setForm({
        period_start: "", period_end: "", billed_kwh: "",
        billed_amount: "", issued_date: "", notes: "",
      });
      await load();
    } catch (e) {
      setFormError(e instanceof ApiError ? e.message : "No se pudo registrar.");
    } finally {
      setSubmitting(false);
    }
  }

  async function onDelete(inv: InvoiceOut) {
    const ok = window.confirm(
      `¿Eliminar la factura del período ${formatDate(inv.period_start)} – ` +
        `${formatDate(inv.period_end)}?`,
    );
    if (!ok) return;
    setDeletingId(inv.id);
    try {
      await api.deleteInvoice(inv.id);
      if (comparison?.period_start === inv.period_start) setComparison(null);
      await load();
    } catch (e) {
      setListError(e instanceof ApiError ? e.message : "No se pudo eliminar.");
    } finally {
      setDeletingId(null);
    }
  }

  async function onCompare(inv: InvoiceOut) {
    setComparingId(inv.id);
    setComparison(null);
    try {
      setComparison(await api.compareInvoice(inv.id));
    } catch (e) {
      setListError(e instanceof ApiError ? e.message : "No se pudo comparar.");
    } finally {
      setComparingId(null);
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <LoadingOverlay
        open={loading && invoices.length === 0}
        message="Cargando facturas…"
        error={!loading && listError && invoices.length === 0 ? listError : null}
        onRetry={load}
      />

      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Facturas</h1>
        <p className="text-sm text-muted-foreground">
          Registra las facturas reales y compáralas con el cálculo de SmartEnergy ML.
        </p>
      </header>

      <MonthlySection months={MONTHS} />

      {/* Registrar factura */}
      <form onSubmit={onSubmit} className="mb-8 rounded-xl border bg-card p-5 shadow-sm">
        <h2 className="mb-1 text-lg font-semibold">Registrar factura</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          El período facturado es independiente del mes calendario.
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Fecha inicial del período">
            <input type="date" required value={form.period_start}
              onChange={(e) => setForm({ ...form, period_start: e.target.value })}
              className="rounded-md border bg-background px-3 py-2" />
          </Field>
          <Field label="Fecha final del período">
            <input type="date" required value={form.period_end}
              onChange={(e) => setForm({ ...form, period_end: e.target.value })}
              className="rounded-md border bg-background px-3 py-2" />
          </Field>
          <Field label="Consumo facturado (kWh)">
            <input type="number" step="0.001" min="0" required value={form.billed_kwh}
              onChange={(e) => setForm({ ...form, billed_kwh: e.target.value })}
              className="rounded-md border bg-background px-3 py-2" />
          </Field>
          <Field label="Valor facturado (COP)">
            <input type="number" step="0.01" min="0" required value={form.billed_amount}
              onChange={(e) => setForm({ ...form, billed_amount: e.target.value })}
              className="rounded-md border bg-background px-3 py-2" />
          </Field>
          <Field label="Fecha de emisión (opcional)">
            <input type="date" value={form.issued_date}
              onChange={(e) => setForm({ ...form, issued_date: e.target.value })}
              className="rounded-md border bg-background px-3 py-2" />
          </Field>
          <Field label="Observaciones (opcional)">
            <input type="text" value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="rounded-md border bg-background px-3 py-2" />
          </Field>
        </div>
        {formError ? <p className="mt-3 text-sm text-destructive">{formError}</p> : null}
        {success ? (
          <p className="mt-3 text-sm text-green-600 dark:text-green-500">{success}</p>
        ) : null}
        <Button type="submit" disabled={submitting} className="mt-4">
          {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Registrar factura
        </Button>
      </form>

      {/* Lista */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">Facturas registradas</h2>
        {loading ? (
          <div className="rounded-lg border bg-card p-6 text-sm text-muted-foreground">
            Cargando…
          </div>
        ) : null}
        {!loading && listError ? (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
            {listError}
          </div>
        ) : null}
        {!loading && !listError && invoices.length === 0 ? (
          <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
            Aún no hay facturas registradas.
          </div>
        ) : null}
        {!loading && invoices.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border bg-card">
            <table className="w-full min-w-[560px] text-sm">
              <thead className="border-b text-left text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium whitespace-nowrap">Período</th>
                  <th className="px-4 py-3 font-medium whitespace-nowrap">kWh facturado</th>
                  <th className="px-4 py-3 font-medium whitespace-nowrap">Valor</th>
                  <th className="px-4 py-3 font-medium text-right whitespace-nowrap">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {pager.rows.map((inv) => (
                  <tr key={inv.id} className="border-b last:border-0">
                    <td className="px-4 py-3 whitespace-nowrap">
                      {formatDate(inv.period_start)} – {formatDate(inv.period_end)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">{formatKwh(inv.billed_kwh)}</td>
                    <td className="px-4 py-3 whitespace-nowrap">{formatCOP(inv.billed_amount)}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="outline" size="sm" onClick={() => onCompare(inv)}
                          disabled={comparingId === inv.id}>
                          {comparingId === inv.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : "Comparar"}
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => onDelete(inv)}
                          disabled={deletingId === inv.id} aria-label="Eliminar factura">
                          {deletingId === inv.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : <Trash2 className="h-4 w-4 text-destructive" />}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {!loading && invoices.length > 10 ? (
          <PaginationBar
            page={pager.page}
            totalPages={pager.totalPages}
            total={pager.total}
            onPrev={pager.goPrev}
            onNext={pager.goNext}
            unit={["factura", "facturas"]}
          />
        ) : null}

        {comparison ? <ComparisonCard c={comparison} /> : null}
      </section>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium">{label}</span>
      {children}
    </label>
  );
}

function ComparisonCard({ c }: { c: InvoiceComparisonOut }) {
  return (
    <div className="mt-6 rounded-xl border bg-card p-5 shadow-sm">
      <h3 className="mb-1 text-base font-semibold">
        Comparación · {formatDate(c.period_start)} – {formatDate(c.period_end)}
      </h3>
      {!c.calculated_sufficient ? (
        <p className="mb-3 rounded-md border border-amber-500/40 bg-amber-500/10 p-2 text-sm text-muted-foreground">
          Información insuficiente para calcular este período con las lecturas
          disponibles.
        </p>
      ) : c.calculated_estimated ? (
        <p className="mb-3 rounded-md border border-amber-500/40 bg-amber-500/10 p-2 text-sm text-muted-foreground">
          El cálculo incluye interpolación en los bordes del período (estimado).
        </p>
      ) : null}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border p-3">
          <p className="text-xs text-muted-foreground">Consumo</p>
          <p className="text-sm">Calculado: <strong>{formatKwh(c.calculated_kwh)}</strong></p>
          <p className="text-sm">Facturado: <strong>{formatKwh(c.billed_kwh)}</strong></p>
          <p className="text-sm text-muted-foreground">
            Diferencia: {formatKwh(c.kwh_diff)}
            {c.kwh_diff_pct !== null ? ` (${c.kwh_diff_pct}%)` : " (—)"}
          </p>
        </div>
        <div className="rounded-lg border p-3">
          <p className="text-xs text-muted-foreground">Costo</p>
          <p className="text-sm">Calculado: <strong>{formatCOP(c.calculated_cost)}</strong></p>
          <p className="text-sm">Facturado: <strong>{formatCOP(c.billed_amount)}</strong></p>
          <p className="text-sm text-muted-foreground">
            Diferencia: {formatCOP(c.cost_diff)}
            {c.cost_diff_pct !== null ? ` (${c.cost_diff_pct}%)` : " (—)"}
          </p>
        </div>
      </div>
    </div>
  );
}

function MonthlySection({ months }: { months: string[] }) {
  // Año/mes por defecto se fijan en el cliente (useEffect), no en el prerender.
  const [year, setYear] = useState(2026);
  const [month, setMonth] = useState(1);
  const [result, setResult] = useState<PeriodConsumptionOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const now = new Date();
    setYear(now.getFullYear());
    setMonth(now.getMonth() + 1);
  }, []);

  async function query() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await api.getMonthly(year, month));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error al consultar el mes.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mb-8 rounded-xl border bg-card p-5 shadow-sm">
      <h2 className="mb-1 text-lg font-semibold">Consumo por mes calendario</h2>
      <p className="mb-4 text-sm text-muted-foreground">
        Del día 1 al último del mes. Es independiente del ciclo real de facturación.
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium">Año</span>
          <input type="number" value={year} min={2000} max={2100}
            onChange={(e) => setYear(Number(e.target.value))}
            className="w-28 rounded-md border bg-background px-3 py-2" />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium">Mes</span>
          <select value={month} onChange={(e) => setMonth(Number(e.target.value))}
            className="rounded-md border bg-background px-3 py-2">
            {months.map((m, i) => (
              <option key={i} value={i + 1}>{m}</option>
            ))}
          </select>
        </label>
        <Button type="button" onClick={query} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          Consultar
        </Button>
      </div>
      {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
      {result ? (
        result.sufficient ? (
          <div className="mt-4 rounded-lg border p-3 text-sm">
            <p>Consumo calculado: <strong>{formatKwh(result.kwh)}</strong></p>
            <p>Costo calculado: <strong>{formatCOP(result.estimated_cost)}</strong></p>
            {result.estimated ? (
              <p className="mt-1 text-xs text-amber-600 dark:text-amber-500">
                Incluye interpolación: {Math.round(result.estimated_fraction * 100)}% del
                consumo es estimado.
              </p>
            ) : (
              <p className="mt-1 text-xs text-muted-foreground">
                Cálculo sobre lecturas completas (sin interpolación).
              </p>
            )}
          </div>
        ) : (
          <p className="mt-4 rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-muted-foreground">
            Información insuficiente: no hay lecturas que cubran ese mes.
          </p>
        )
      ) : null}
    </div>
  );
}
