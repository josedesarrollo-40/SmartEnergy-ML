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
