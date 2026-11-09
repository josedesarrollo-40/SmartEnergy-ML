"use client";

import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";

/**
 * Paginación de cliente reutilizable.
 *
 * Recibe la lista YA filtrada y ordenada; solo corta la página visible y
 * expone los controles. Reiniciar a la página 1 cuando cambian los filtros se
 * resuelve con `resetKey`: cualquier cambio de ese valor vuelve a la primera
 * página, por lo que filtros y orden se conservan entre páginas de forma
 * natural (el padre mantiene el orden; esto solo pagina).
 */
export function usePagination<T>(
  items: T[],
  pageSize: number,
  resetKey?: unknown,
) {
  const [page, setPage] = useState(1);

  // Al cambiar filtro/orden (resetKey), volver a la primera página. Se ajusta
  // DURANTE el render (patrón recomendado por React) en lugar de un efecto, para
  // no provocar renders en cascada.
  const [prevKey, setPrevKey] = useState(resetKey);
  if (prevKey !== resetKey) {
    setPrevKey(resetKey);
    setPage(1);
  }

  const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
  const currentPage = Math.min(page, totalPages);

  const rows = useMemo(
    () => items.slice((currentPage - 1) * pageSize, currentPage * pageSize),
    [items, currentPage, pageSize],
  );

  return {
    rows,
    page: currentPage,
    totalPages,
    total: items.length,
    setPage,
    goPrev: () => setPage((p) => Math.max(1, p - 1)),
    goNext: () => setPage((p) => Math.min(totalPages, p + 1)),
  };
}

interface PaginationBarProps {
  page: number;
  totalPages: number;
  total: number;
  onPrev: () => void;
  onNext: () => void;
  /** Singular/plural de la entidad listada, p. ej. "registro" / "registros". */
  unit?: [singular: string, plural: string];
}

/**
 * Barra de paginación con "Anterior / Siguiente", página actual y total de
 * registros. Responsive: apila los controles bajo el texto en móvil.
 */
export function PaginationBar({
  page,
  totalPages,
  total,
  onPrev,
  onNext,
  unit = ["registro", "registros"],
}: PaginationBarProps) {
  return (
    <div className="mt-3 flex flex-col items-center justify-between gap-3 text-sm sm:flex-row">
      <p className="text-muted-foreground">
        Página <span className="font-medium text-foreground">{page}</span> de{" "}
        <span className="font-medium text-foreground">{totalPages}</span>
        {" · "}
        {total} {total === 1 ? unit[0] : unit[1]}
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onPrev}
          disabled={page <= 1}
        >
          <ChevronLeft className="h-4 w-4" aria-hidden />
          Anterior
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onNext}
          disabled={page >= totalPages}
        >
          Siguiente
          <ChevronRight className="h-4 w-4" aria-hidden />
        </Button>
      </div>
    </div>
  );
}
