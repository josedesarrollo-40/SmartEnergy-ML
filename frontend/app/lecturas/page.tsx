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
    observed_now: false,
  });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [confirmingId, setConfirmingId] = useState<number | null>(null);
  const [onlyPending, setOnlyPending] = useState(false);

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
    const all = readings.map((r, i) => {
      const prev = i > 0 ? readings[i - 1] : null;
      const consumo =
        prev && r.value_kwh >= prev.value_kwh ? r.value_kwh - prev.value_kwh : null;
      return { reading: r, consumo };
    });
    return onlyPending
      ? all.filter((x) => x.reading.date_confidence === "pending")
      : all;
  }, [readings, onlyPending]);

  async function onConfirm(r: ReadingOut) {
    const ok = window.confirm(
      `¿Confirmas que la fecha ${formatDate(r.reading_date)} de esta lectura ` +
        `(${formatKwh(r.value_kwh)}) es correcta?`,
    );
    if (!ok) return;
    setConfirmingId(r.id);
    try {
      await api.confirmReadingDate(r.id);
      await load();
    } catch (e) {
      setListError(e instanceof ApiError ? e.message : "No se pudo confirmar.");
    } finally {
      setConfirmingId(null);
    }
  }

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

    // observed_now solo tiene efecto (verified) si además hay hora real.
    if (form.observed_now && !form.reading_time) {
      return setFormError(
        "Para marcar la lectura como observada ahora, indica también la hora real.",
      );
    }

    const payload: ReadingCreate = {
      reading_date: form.reading_date,
      reading_time: form.reading_time || null,
      value_kwh: value,
      note: form.note.trim() || null,
      observed_now: form.observed_now && !!form.reading_time,
    };

    setSubmitting(true);
    try {
      await api.createReading(payload);
      setSuccess("Lectura registrada.");
      setForm({
        reading_date: todayISO(),
        reading_time: "",
        value_kwh: "",
        note: "",
        observed_now: false,
      });
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
            <span className="font-medium">Hora real (opcional)</span>
            <div className="flex gap-2">
              <input
                type="time"
                step="1"
                value={form.reading_time}
                onChange={(e) => setForm({ ...form, reading_time: e.target.value })}
                className="w-full rounded-md border bg-background px-3 py-2"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() =>
                  setForm({
                    ...form,
                    reading_time: new Date().toTimeString().slice(0, 8),
                  })
                }
              >
                Ahora
              </Button>
            </div>
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

        <label className="mt-4 flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.observed_now}
            onChange={(e) => setForm({ ...form, observed_now: e.target.checked })}
            className="mt-0.5"
          />
          <span>
            La observé ahora en el medidor (fecha y hora reales).
            <span className="block text-xs text-muted-foreground">
              Marca la lectura como verificada. Requiere indicar la hora real.
            </span>
          </span>
        </label>

        {/* Confirmación de datos antes de guardar */}
        {form.value_kwh && form.reading_date ? (
          <div className="mt-4 rounded-md border bg-muted/40 p-3 text-sm">
            <p className="font-medium">Vas a registrar:</p>
            <p className="text-muted-foreground">
              {form.reading_date}
              {form.reading_time ? ` ${form.reading_time}` : " (sin hora)"} ·{" "}
              {form.value_kwh} kWh
              {" · "}
              {form.observed_now && form.reading_time
                ? "verificada"
                : "confirmada"}
            </p>
          </div>
        ) : null}

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
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Historial</h2>
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={onlyPending}
              onChange={(e) => setOnlyPending(e.target.checked)}
            />
            Solo pendientes
          </label>
        </div>

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
                  <th className="px-4 py-3 font-medium">Confianza</th>
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
                    <td className="px-4 py-3">
                      <ConfidenceBadge value={r.date_confidence} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{r.note ?? "—"}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {r.date_confidence === "pending" ? (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onConfirm(r)}
                            disabled={confirmingId === r.id}
                          >
                            {confirmingId === r.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                            ) : (
                              "Confirmar fecha"
                            )}
                          </Button>
                        ) : null}
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
                      </div>
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

const CONFIDENCE_STYLE: Record<string, string> = {
  verified: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400",
  confirmed: "bg-blue-500/15 text-blue-700 dark:text-blue-400",
  inferred: "bg-amber-500/15 text-amber-700 dark:text-amber-500",
  pending: "bg-muted text-muted-foreground",
};

const CONFIDENCE_LABEL: Record<string, string> = {
  verified: "Verificada",
  confirmed: "Confirmada",
  inferred: "Inferida",
  pending: "Pendiente",
};

function ConfidenceBadge({ value }: { value: string }) {
  const style = CONFIDENCE_STYLE[value] ?? "bg-muted text-muted-foreground";
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${style}`}
    >
      {CONFIDENCE_LABEL[value] ?? value}
    </span>
  );
}
