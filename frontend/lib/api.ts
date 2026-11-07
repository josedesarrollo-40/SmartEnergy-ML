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
    let detail = `Error ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* respuesta sin cuerpo JSON */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => getJson<{ status: string }>("/health"),
  getSummary: () => getJson<SummaryOut>("/api/analytics/summary"),
  listReadings: () => getJson<ReadingOut[]>("/api/readings"),
  getTariff: () => getJson<TariffOut>("/api/tariff"),
};

export { API_URL };
