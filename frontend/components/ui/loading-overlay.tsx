"use client";

import { useEffect } from "react";
import { AlertTriangle, Loader2, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { LogoMark } from "@/components/logo";

interface LoadingOverlayProps {
  /** Si true, se muestra el modal centrado con fondo oscurecido. */
  open: boolean;
  /** Mensaje contextual: "Cargando información…", "Recuperando datos…". */
  message?: string;
  /** Mensaje de error; si está presente se muestra el estado de error. */
  error?: string | null;
  /** Si se pasa, muestra el botón "Reintentar" en el estado de error. */
  onRetry?: () => void;
}

/**
 * Modal de carga elegante y coherente con la identidad de SmartEnergy ML.
 *
 * - Centrado, con fondo ligeramente oscurecido (backdrop blur).
 * - Spinner sutil mientras se espera al backend.
 * - Al terminar la operación, el padre pone open=false y se cierra solo.
 * - Si hay error, muestra el mensaje y, cuando aplica, un botón "Reintentar".
 *
 * Respeta prefers-reduced-motion: el spinner no gira si el usuario lo pidió.
 */
export function LoadingOverlay({
  open,
  message = "Cargando información…",
  error,
  onRetry,
}: LoadingOverlayProps) {
  // Evita el scroll del fondo mientras el modal está abierto.
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!open) return null;

  const isError = Boolean(error);

  return (
    <div
      role={isError ? "alertdialog" : "status"}
      aria-live="polite"
      aria-busy={!isError}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      {/* Backdrop oscurecido */}
      <div
        aria-hidden
        className="absolute inset-0 bg-foreground/40 backdrop-blur-sm"
      />

      {/* Tarjeta central */}
      <div className="relative w-full max-w-sm rounded-2xl border bg-card p-6 text-center shadow-xl">
        {isError ? (
          <>
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
              <AlertTriangle className="h-6 w-6" aria-hidden />
            </span>
            <p className="mt-4 font-semibold text-foreground">
              No se pudo completar la operación
            </p>
            <p className="mt-1 text-sm text-muted-foreground">{error}</p>
            {onRetry ? (
              <Button onClick={onRetry} className="mt-5">
                <RefreshCw className="h-4 w-4" aria-hidden />
                Reintentar
              </Button>
            ) : null}
          </>
        ) : (
          <>
            <span className="relative mx-auto flex h-14 w-14 items-center justify-center">
              <Loader2
                className="absolute h-14 w-14 animate-spin text-primary/70 motion-reduce:animate-none"
                aria-hidden
              />
              <LogoMark className="h-7 w-7" />
            </span>
            <p className="mt-4 font-semibold text-foreground">{message}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Conectando con SmartEnergy ML…
            </p>
          </>
        )}
      </div>
    </div>
  );
}
