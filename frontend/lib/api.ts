// Cliente HTTP al backend FastAPI. La URL viene de NEXT_PUBLIC_API_URL.
import { localTodayISO } from "@/lib/format";
import type {
  DataQualityOut,
  IntervalWeatherRow,
  InvoiceComparisonOut,
  InvoiceOut,
  PeriodConsumptionOut,
  ReadingOut,
  SummaryOut,
  TariffOut,
  WeatherBackfillResult,
} from "@/lib/types";

export interface InvoiceCreate {
  period_start: string;
  period_end: string;
  billed_kwh: number;
  billed_amount: number;
  issued_date?: string | null;
  notes?: string | null;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function extractDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    const d = body?.detail;
    if (typeof d === "string") return d;
    // FastAPI 422: detail es una lista de errores de validación.
    if (Array.isArray(d) && d.length > 0) {
      return d
        .map((e) => e?.msg ?? "Dato inválido")
        .join("; ");
    }
  } catch {
    /* sin cuerpo JSON */
  }
  return `Error ${res.status}`;
}

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      "No se pudo conectar con el servidor. ¿Está corriendo el backend?",
    );
  }
  if (!res.ok) {
    throw new ApiError(await extractDetail(res), res.status);
  }
  return res.json() as Promise<T>;
}

export interface ReadingCreate {
  reading_date: string; // YYYY-MM-DD
  reading_time?: string | null; // HH:MM o HH:MM:SS
  value_kwh: number;
  note?: string | null;
  observed_now?: boolean;
}

export interface TariffUpdate {
  price_per_kwh: number;
  currency: string;
  valid_from?: string | null; // YYYY-MM-DD
}

async function del(path: string): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { method: "DELETE", cache: "no-store" });
  } catch {
    throw new ApiError("No se pudo conectar con el servidor.");
  }
  if (!res.ok && res.status !== 204) {
    throw new ApiError(await extractDetail(res), res.status);
  }
}

export const api = {
  health: () => getJson<{ status: string }>("/health"),
  getSummary: () => getJson<SummaryOut>("/api/analytics/summary"),
  getDataQuality: () => getJson<DataQualityOut>("/api/analytics/data-quality"),
  listReadings: () => getJson<ReadingOut[]>("/api/readings"),
  listReadingsRange: (start?: string, end?: string) => {
    const qs = new URLSearchParams();
    if (start) qs.set("start", start);
    if (end) qs.set("end", end);
    const q = qs.toString();
    return getJson<ReadingOut[]>(`/api/readings${q ? `?${q}` : ""}`);
  },
  getTariff: () => getJson<TariffOut>("/api/tariff"),
  updateTariff: (payload: TariffUpdate) =>
    getJson<TariffOut>("/api/tariff", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  createReading: (payload: ReadingCreate) =>
    getJson<ReadingOut>("/api/readings", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  deleteReading: (id: number) => del(`/api/readings/${id}`),
  confirmReadingDate: (id: number) =>
    getJson<ReadingOut>(`/api/readings/${id}/confirm-date`, { method: "PATCH" }),
  listInvoices: () => getJson<InvoiceOut[]>("/api/invoices"),
  createInvoice: (payload: InvoiceCreate) =>
    getJson<InvoiceOut>("/api/invoices", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  deleteInvoice: (id: number) => del(`/api/invoices/${id}`),
  compareInvoice: (id: number) =>
    getJson<InvoiceComparisonOut>(`/api/invoices/${id}/comparison`),
  getMonthly: (year: number, month: number) =>
    getJson<PeriodConsumptionOut>(`/api/analytics/monthly?year=${year}&month=${month}`),
  // Consumo acumulado del mes EN CURSO: desde el día 1 del mes hasta la fecha
  // indicada (hoy por defecto). Reutiliza /period, que respeta tarifa histórica
  // y marca "sufficient"/"estimated". No es el acumulado histórico.
  getCurrentMonthToDate: (today?: string) => {
    const d = today ?? localTodayISO();
    const start = `${d.slice(0, 7)}-01`; // YYYY-MM-01
    return getJson<PeriodConsumptionOut>(
      `/api/analytics/period?start=${start}&end=${d}`,
    );
  },
  // Consumo y costo de un rango arbitrario. El backend aplica la tarifa
  // histórica vigente en cada tramo; el frontend NO recalcula el costo.
  getPeriod: (start: string, end: string) =>
    getJson<PeriodConsumptionOut>(
      `/api/analytics/period?start=${start}&end=${end}`,
    ),
  // Clima por intervalo. Solo LECTURA de lo ya capturado por el backend:
  // consultar esta ruta NO dispara llamadas a Open-Meteo.
  listIntervalWeather: () =>
    getJson<IntervalWeatherRow[]>("/api/weather/intervals"),
  // Acción explícita del usuario: reintenta los intervalos pendientes/fallidos.
  recoverWeather: () =>
    getJson<WeatherBackfillResult>("/api/weather/recover", { method: "POST" }),
};

export { API_URL };
