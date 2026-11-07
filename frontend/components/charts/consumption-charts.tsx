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
  label: string; // "01 ene → 11 ene"
  kwh: number;
}

export interface CumulativePoint {
  date: string; // etiqueta de fecha corta
  value: number;
}

const CO = "es-CO";
const nf = new Intl.NumberFormat(CO, { maximumFractionDigits: 2 });

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
        <Tooltip
          formatter={(v) => [formatKwh(v as number), "Consumo"]}
          labelFormatter={(l) => `Intervalo: ${l}`}
        />
        <Bar dataKey="kwh" fill="#eab308" radius={[4, 4, 0, 0]} />
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
        />
        <Area
          type="monotone"
          dataKey="value"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.15}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
