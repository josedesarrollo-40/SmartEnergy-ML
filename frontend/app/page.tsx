import { Zap } from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <div className="flex items-center gap-3">
        <Zap className="h-10 w-10 text-yellow-500" aria-hidden />
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          SmartEnergy ML
        </h1>
      </div>
      <p className="max-w-md text-muted-foreground">
        Plataforma de análisis y predicción del consumo eléctrico residencial.
      </p>
      <p className="text-sm text-muted-foreground">
        Frontend inicial. La conexión con la API y el panel de consumo llegan en
        las siguientes etapas.
      </p>
    </main>
  );
}
