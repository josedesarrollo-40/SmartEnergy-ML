/**
 * Logo propio de SmartEnergy ML.
 * Símbolo: un rayo (energía eléctrica) sobre un nodo de análisis con puntos
 * de datos (análisis inteligente). SVG vectorial, sin imágenes externas,
 * legible en tamaños pequeños. Usa currentColor para heredar el color.
 */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* nodo/círculo de análisis */}
      <circle cx="16" cy="16" r="14" className="fill-primary" />
      {/* rayo de energía */}
      <path
        d="M17.5 7 L10 17.5 h4.2 L13.5 25 L22 13.8 h-4.6 Z"
        className="fill-primary-foreground"
      />
      {/* tres puntos de datos (análisis) */}
      <circle cx="7" cy="9" r="1.3" className="fill-primary-foreground/70" />
      <circle cx="25" cy="22" r="1.3" className="fill-primary-foreground/70" />
      <circle cx="24.5" cy="8.5" r="1" className="fill-primary-foreground/60" />
    </svg>
  );
}
