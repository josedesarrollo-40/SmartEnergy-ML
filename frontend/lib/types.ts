// Tipos espejo de los esquemas Pydantic del backend (FastAPI).
// Mantener sincronizados con backend/app/schemas/.

export interface ReadingOut {
  id: number;
  reading_date: string; // YYYY-MM-DD
  reading_time: string; // HH:MM:SS
  value_kwh: number;
  note: string | null;
  source: string;
  date_confidence: string; // verified | confirmed | inferred | pending
  time_known: boolean;
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

export interface DataQualityOut {
  total_readings: number;
  first_date: string | null;
  last_date: string | null;
  span_days: number;
  observed_days: number;
  interpolated_days: number;
  missing_days: number;
  time_known_count: number;
  confidence_counts: Record<string, number>;
  source_counts: Record<string, number>;
  irregular_intervals: { from: string; to: string; days: number }[];
  pending_or_inferred: number;
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
