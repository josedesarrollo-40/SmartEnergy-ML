// Tipos espejo de los esquemas Pydantic del backend (FastAPI).
// Mantener sincronizados con backend/app/schemas/.

export interface ReadingOut {
  id: number;
  reading_date: string; // YYYY-MM-DD
  value_kwh: number;
  note: string | null;
  created_at: string; // ISO datetime
}

export interface TariffOut {
  id: number | null;
  price_per_kwh: number;
  currency: string;
  valid_from: string; // YYYY-MM-DD
  created_at: string | null;
  persisted: boolean;
}

export interface SummaryOut {
  last_reading_date: string | null;
  last_reading_value: number | null;
  total_kwh: number;
  avg_daily_kwh: number;
  estimated_cost: number;
  currency: string;
  monthly_projection_kwh: number;
  monthly_projection_cost: number;
}
