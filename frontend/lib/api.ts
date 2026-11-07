// Cliente HTTP al backend FastAPI. La URL viene de NEXT_PUBLIC_API_URL.
import type { ReadingOut, SummaryOut, TariffOut } from "@/lib/types";

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
  value_kwh: number;
  note?: string | null;
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
};

export { API_URL };
