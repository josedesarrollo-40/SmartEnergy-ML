// Formato para Colombia: COP, kWh, fechas.
const CO = "es-CO";

export function formatCOP(value: number): string {
  return new Intl.NumberFormat(CO, {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatKwh(value: number, decimals = 2): string {
  return `${new Intl.NumberFormat(CO, {
    maximumFractionDigits: decimals,
  }).format(value)} kWh`;
}

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso.length <= 10 ? `${iso}T00:00:00` : iso);
  return new Intl.DateTimeFormat(CO, {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(d);
}

// Fecha corta "01 ene" para ejes y etiquetas de gráficas.
export function formatDateShort(iso: string): string {
  const d = new Date(iso.length <= 10 ? `${iso}T00:00:00` : iso);
  return new Intl.DateTimeFormat(CO, { day: "2-digit", month: "short" }).format(d);
}

// Fecha de HOY en zona local (no UTC): toISOString daría el día siguiente
// por la noche en -05. Devuelve "YYYY-MM-DD".
export function localTodayISO(d: Date = new Date()): string {
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}

// Nombre del mes y año a partir de una fecha ISO (YYYY-MM-DD), p. ej.
// "noviembre de 2026". No usa new Date() sin argumento, así que es seguro de
// evaluar durante el render de componentes cliente.
export function monthLabelFrom(iso: string): string {
  return new Intl.DateTimeFormat(CO, { month: "long", year: "numeric" }).format(
    new Date(`${iso.slice(0, 10)}T00:00:00`),
  );
}
