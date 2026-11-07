"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatKwh } from "@/lib/format";

export interface IntervalPoint {
  label: string; // etiqueta corta del eje, p. ej. "26 oct → 04 nov"
  start: string; // fecha inicial legible
  end: string; // fecha final legible
  kwh: number;
}

export interface CumulativePoint {
  date: string; // etiqueta de fecha corta
  value: number;
}

const CO = "es-CO";
const nf = new Intl.NumberFormat(CO, { maximumFractionDigits: 2 });

function IntervalTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: IntervalPoint }>;
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-lg border bg-card p-3 text-sm shadow-md">
      <p className="font-medium">{formatKwh(p.kwh)}</p>
      <p className="text-muted-foreground">Desde: {p.start}</p>
      <p className="text-muted-foreground">Hasta: {p.end}</p>
    </div>
  );
}

export function IntervalChart({ data }: { data: IntervalPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
        <YAxis
          tick={{ fontSize: 11 }}
          tickFormatter={(v) => nf.format(v as number)}
          width={56}
        />
        <Tooltip content={<IntervalTooltip />} cursor={{ fill: "rgba(0,0,0,0.04)" }} />
        <Bar dataKey="kwh" fill="var(--chart-2)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function CumulativeChart({ data }: { data: CumulativePoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
        <YAxis
          tick={{ fontSize: 11 }}
          tickFormatter={(v) => nf.format(v as number)}
          width={64}
        />
        <Tooltip
          formatter={(v) => [formatKwh(v as number), "Lectura"]}
          labelFormatter={(l) => `Fecha: ${l}`}
          contentStyle={{ borderRadius: 8 }}
        />
        <Area
          type="monotone"
          dataKey="value"
          stroke="var(--chart-1)"
          fill="var(--chart-1)"
          fillOpacity={0.15}
          dot={{ r: 3, fill: "var(--chart-1)" }}
          activeDot={{ r: 5 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
