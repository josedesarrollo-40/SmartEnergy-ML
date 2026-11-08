"use client";

import { useCallback, useEffect, useState } from "react";
import { Info, Loader2, Save } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api, ApiError, type TariffUpdate } from "@/lib/api";
import { formatCOP, formatDate } from "@/lib/format";
import type { TariffOut } from "@/lib/types";

function todayISO(): string {
  // Fecha LOCAL (no UTC): toISOString daría el día siguiente por la noche en -05.
  const d = new Date();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}

export default function TarifasPage() {
  const [tariff, setTariff] = useState<TariffOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [form, setForm] = useState({ price_per_kwh: "", valid_from: "" });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      setTariff(await api.getTariff());
    } catch (e) {
      setLoadError(e instanceof ApiError ? e.message : "Error al cargar la tarifa.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Fecha de vigencia por defecto = hoy, solo en el cliente.
  useEffect(() => {
    setForm((f) => (f.valid_from ? f : { ...f, valid_from: todayISO() }));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSuccess(null);

    const price = Number(form.price_per_kwh);
    if (form.price_per_kwh === "" || Number.isNaN(price)) {
      return setFormError("Indica el precio por kWh.");
    }
    if (price <= 0) return setFormError("El precio debe ser mayor que cero.");
    if (!form.valid_from) return setFormError("Indica la fecha de inicio de vigencia.");

    const payload: TariffUpdate = {
      price_per_kwh: price,
      currency: "COP",
      valid_from: form.valid_from,
    };

    setSaving(true);
    try {
      await api.updateTariff(payload);
      setSuccess("Tarifa guardada. Se registró como una nueva tarifa histórica.");
      setForm({ price_per_kwh: "", valid_from: todayISO() });
      await load();
    } catch (e) {
      setFormError(e instanceof ApiError ? e.message : "No se pudo guardar la tarifa.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Tarifas</h1>
        <p className="text-sm text-muted-foreground">
          Consulta la tarifa vigente y registra nuevas tarifas por kWh.
        </p>
      </header>

      {/* Tarifa vigente */}
      <section className="mb-8">
        <h2 className="mb-3 text-lg font-semibold">Tarifa vigente</h2>

        {loading ? (
          <div className="h-28 animate-pulse rounded-xl border bg-muted/40" aria-hidden />
        ) : null}

        {!loading && loadError ? (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
            {loadError}
          </div>
        ) : null}

        {!loading && !loadError && tariff ? (
          <div className="rounded-xl border bg-card p-5 shadow-sm">
            <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
              <div>
                <p className="text-sm text-muted-foreground">Precio por kWh</p>
                <p className="text-2xl font-bold">{formatCOP(tariff.price_per_kwh)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Moneda</p>
                <p className="font-medium">{tariff.currency}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Vigente desde</p>
                <p className="font-medium">{formatDate(tariff.valid_from)}</p>
              </div>
            </div>

            {!tariff.persisted ? (
              <div className="mt-4 flex items-start gap-2 rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" aria-hidden />
                <span className="text-muted-foreground">
                  Esta es la <strong>tarifa predeterminada</strong> (en memoria). Aún
                  no hay ninguna tarifa guardada en la base de datos. Guarda una para
                  fijarla.
                </span>
              </div>
            ) : null}
          </div>
        ) : null}
      </section>

      {/* Actualizar tarifa */}
      <form onSubmit={onSubmit} className="mb-8 rounded-xl border bg-card p-5 shadow-sm">
        <h2 className="mb-1 text-lg font-semibold">Registrar nueva tarifa</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Guardar no borra la tarifa anterior: se registra una nueva tarifa histórica
          con su fecha de vigencia.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium">Precio por kWh (COP)</span>
            <input
              type="number"
              step="0.0001"
              min="0"
              inputMode="decimal"
              value={form.price_per_kwh}
              onChange={(e) => setForm({ ...form, price_per_kwh: e.target.value })}
              placeholder="Ej. 997.92"
              className="rounded-md border bg-background px-3 py-2"
              required
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium">Vigente desde</span>
            <input
              type="date"
              value={form.valid_from}
              onChange={(e) => setForm({ ...form, valid_from: e.target.value })}
              className="rounded-md border bg-background px-3 py-2"
              required
            />
          </label>
        </div>

        {formError ? <p className="mt-3 text-sm text-destructive">{formError}</p> : null}
        {success ? (
          <p className="mt-3 text-sm text-green-600 dark:text-green-500">{success}</p>
        ) : null}

        <Button type="submit" disabled={saving} className="mt-4">
          {saving ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          ) : (
            <Save className="h-4 w-4" aria-hidden />
          )}
          Guardar tarifa
        </Button>
      </form>

      {/* Historial: pendiente de endpoint en el backend */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">Historial de tarifas</h2>
        <div className="rounded-lg border border-dashed bg-card p-6 text-sm text-muted-foreground">
          El backend aún no expone un endpoint para listar el historial de tarifas
          (solo <code className="rounded bg-muted px-1 py-0.5">GET /api/tariff</code>{" "}
          devuelve la vigente). Esta sección queda preparada para mostrar la tabla
          cuando exista ese contrato.
        </div>
      </section>
    </div>
  );
}
