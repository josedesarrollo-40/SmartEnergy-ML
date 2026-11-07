"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api, ApiError, type ReadingCreate } from "@/lib/api";
import { formatDate, formatKwh } from "@/lib/format";
import type { ReadingOut } from "@/lib/types";

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function LecturasPage() {
  const [readings, setReadings] = useState<ReadingOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  // reading_date se fija en el cliente (useEffect) para no evaluar new Date()
  // durante el prerender estático de Next.
  const [form, setForm] = useState({
    reading_date: "",
    reading_time: "",
    value_kwh: "",
    note: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [deletingId, setDeletingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setListError(null);
    try {
      setReadings(await api.listReadings());
    } catch (e) {
      setListError(e instanceof ApiError ? e.message : "Error al cargar.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Fecha por defecto = hoy, solo en el cliente.
  useEffect(() => {
    setForm((f) => (f.reading_date ? f : { ...f, reading_date: todayISO() }));
  }, []);

  // Consumo por intervalo: diferencia con la lectura anterior (orden ascendente).
  const rows = useMemo(() => {
    return readings.map((r, i) => {
      const prev = i > 0 ? readings[i - 1] : null;
      const consumo =
        prev && r.value_kwh >= prev.value_kwh ? r.value_kwh - prev.value_kwh : null;
      return { reading: r, consumo };
    });
  }, [readings]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSuccess(null);

    const value = Number(form.value_kwh);
    if (!form.reading_date) return setFormError("Indica la fecha de la lectura.");
    if (form.value_kwh === "" || Number.isNaN(value)) {
      return setFormError("Indica un valor numérico para la lectura.");
    }
    if (value < 0) return setFormError("El valor no puede ser negativo.");

    const payload: ReadingCreate = {
      reading_date: form.reading_date,
      reading_time: form.reading_time || null,
      value_kwh: value,
      note: form.note.trim() || null,
    };

    setSubmitting(true);
    try {
      await api.createReading(payload);
      setSuccess("Lectura registrada.");
      setForm({ reading_date: todayISO(), reading_time: "", value_kwh: "", note: "" });
      await load();
    } catch (e) {
      setFormError(e instanceof ApiError ? e.message : "No se pudo registrar.");
    } finally {
      setSubmitting(false);
    }
  }

  async function onDelete(r: ReadingOut) {
    const ok = window.confirm(
      `¿Eliminar la lectura del ${formatDate(r.reading_date)} (${formatKwh(r.value_kwh)})?`,
    );
    if (!ok) return;
    setDeletingId(r.id);
    try {
      await api.deleteReading(r.id);
      await load();
    } catch (e) {
      setListError(e instanceof ApiError ? e.message : "No se pudo eliminar.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Lecturas</h1>
        <p className="text-sm text-muted-foreground">
          Registra las lecturas del contador y consulta el historial.
        </p>
      </header>

      {/* Formulario de registro */}
      <form
        onSubmit={onSubmit}
        className="mb-8 rounded-xl border bg-card p-5 shadow-sm"
      >
        <h2 className="mb-4 text-lg font-semibold">Nueva lectura</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium">Fecha</span>
            <input
              type="date"
              value={form.reading_date}
              onChange={(e) => setForm({ ...form, reading_date: e.target.value })}
              className="rounded-md border bg-background px-3 py-2"
              required
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium">Hora (opcional)</span>
            <input
              type="time"
              value={form.reading_time}
              onChange={(e) => setForm({ ...form, reading_time: e.target.value })}
              className="rounded-md border bg-background px-3 py-2"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium">Lectura del medidor (kWh)</span>
            <input
              type="number"
              step="0.001"
              min="0"
              inputMode="decimal"
              value={form.value_kwh}
              onChange={(e) => setForm({ ...form, value_kwh: e.target.value })}
              placeholder="Ej. 1234.5"
              className="rounded-md border bg-background px-3 py-2"
              required
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium">Nota (opcional)</span>
            <input
              type="text"
              value={form.note}
              onChange={(e) => setForm({ ...form, note: e.target.value })}
              placeholder="Opcional"
              className="rounded-md border bg-background px-3 py-2"
            />
          </label>
        </div>

        {formError ? (
          <p className="mt-3 text-sm text-destructive">{formError}</p>
        ) : null}
        {success ? (
          <p className="mt-3 text-sm text-green-600 dark:text-green-500">{success}</p>
        ) : null}

        <Button type="submit" disabled={submitting} className="mt-4">
          {submitting ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          ) : (
            <Plus className="h-4 w-4" aria-hidden />
          )}
          Registrar lectura
        </Button>
      </form>

      {/* Historial */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">Historial</h2>

        {loading ? (
          <div className="rounded-lg border bg-card p-6 text-sm text-muted-foreground">
            Cargando lecturas…
          </div>
        ) : null}

        {!loading && listError ? (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
            {listError}
          </div>
        ) : null}

        {!loading && !listError && readings.length === 0 ? (
          <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
            Todavía no hay lecturas registradas.
          </div>
        ) : null}

        {!loading && !listError && readings.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border bg-card">
            <table className="w-full text-sm">
              <thead className="border-b text-left text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Fecha</th>
                  <th className="px-4 py-3 font-medium">Hora</th>
                  <th className="px-4 py-3 font-medium">Lectura (kWh)</th>
                  <th className="px-4 py-3 font-medium">Consumo</th>
                  <th className="px-4 py-3 font-medium">Nota</th>
                  <th className="px-4 py-3 font-medium text-right">Acción</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(({ reading: r, consumo }) => (
                  <tr key={r.id} className="border-b last:border-0">
                    <td className="px-4 py-3">{formatDate(r.reading_date)}</td>
                    <td className="px-4 py-3 tabular-nums">
                      {r.reading_time ? r.reading_time.slice(0, 5) : "—"}
                    </td>
                    <td className="px-4 py-3">{formatKwh(r.value_kwh)}</td>
                    <td className="px-4 py-3">
                      {consumo === null ? "—" : formatKwh(consumo)}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{r.note ?? "—"}</td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(r)}
                        disabled={deletingId === r.id}
                        aria-label="Eliminar lectura"
                      >
                        {deletingId === r.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                        ) : (
                          <Trash2 className="h-4 w-4 text-destructive" aria-hidden />
                        )}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </div>
  );
}
