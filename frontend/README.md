# SmartEnergy ML — Frontend

Interfaz web de SmartEnergy ML. Construida con Next.js (App Router), TypeScript,
Tailwind CSS, shadcn/ui, Recharts y Lucide Icons.

Consume la API REST de FastAPI. No toca la base de datos directamente.

## Requisitos

- Node 18+ (probado con Node 24).
- El backend FastAPI corriendo (ver `../backend`).

## Puesta en marcha

```bash
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev                  # http://localhost:3000
```

`npm run build` genera la build de producción.

## Variables de entorno

| Variable | Para qué |
|---|---|
| `NEXT_PUBLIC_API_URL` | URL base del backend FastAPI |

`.env.local` está excluido de Git. Solo se versiona `.env.example`.

## Estructura

```
frontend/
├── app/
│   ├── layout.tsx       # layout con sidebar
│   ├── page.tsx         # Dashboard (consume /api/analytics/summary)
│   ├── lecturas/        # en construcción
│   ├── tarifas/         # en construcción
│   └── analitica/       # en construcción
├── components/
│   ├── ui/              # shadcn/ui
│   ├── sidebar.tsx      # navegación lateral
│   └── stat-card.tsx    # tarjeta de indicador
├── lib/
│   ├── api.ts           # cliente fetch al backend
│   ├── types.ts         # tipos espejo de los esquemas del backend
│   └── format.ts        # formato COP, kWh y fechas (locale es-CO)
└── .env.example
```

## Estado

- **Dashboard**: muestra las métricas de `/api/analytics/summary` (última lectura,
  consumo, promedio diario, costo, proyección). Maneja carga, error y sin datos.
- **Lecturas / Tarifas / Analítica**: páginas preparadas, en construcción.
- **Gráfica histórica**: pendiente de un endpoint de serie temporal en el backend.

No se usan datos ficticios: todo viene de la API real.
