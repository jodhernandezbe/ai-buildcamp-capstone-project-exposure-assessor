import { useId } from "react";

// The mark is artwork, so its colours are fixed (the same in light and dark), matching
// `public/logo.svg` and `public/favicon.svg`; everything around it uses the design tokens.
const AIR = "#38BDF8";
const SOIL = "#34D399";
const WATER = "#3B82F6";
const INK = "#0F172A";
const RIM = "#F8FAFC";
/** Below this size (px) the detailed mark turns to mush, so the simplified favicon mark is drawn. */
const DETAIL_MIN_PX = 40;

const GLOW = "transition-[filter] duration-300 group-hover:drop-shadow-[0_0_6px_var(--accent)]";

/** The simplified 64-unit mark: squircle, hexagon and the three compartment vectors. */
function SimpleMark() {
  return (
    <>
      <rect x="2" y="2" width="60" height="60" rx="14" fill={INK} />
      <line x1="32" y1="32" x2="32" y2="11" stroke={AIR} strokeWidth="4.5" strokeLinecap="round" />
      <line x1="32" y1="32" x2="50" y2="43" stroke={SOIL} strokeWidth="4.5" strokeLinecap="round" />
      <line x1="32" y1="32" x2="14" y2="43" stroke={WATER} strokeWidth="4.5" strokeLinecap="round" />
      <polygon
        points="32,10 51,21 51,43 32,54 13,43 13,21"
        stroke={RIM}
        strokeWidth="4"
        strokeLinejoin="round"
      />
      <circle cx="32" cy="32" r="5.5" fill="#FFFFFF" />
    </>
  );
}

/** The detailed 512-unit mark: air arc, soil horizon, water wave around the chemical hexagon. */
function DetailedMark({ prefix }: { prefix: string }) {
  const id = (name: string) => `${prefix}-${name}`;
  return (
    <>
      <defs>
        <linearGradient id={id("bg")} x1="64" y1="32" x2="448" y2="480" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor={INK} />
          <stop offset="50%" stopColor="#1E293B" />
          <stop offset="100%" stopColor="#090D16" />
        </linearGradient>
        <linearGradient id={id("air")} x1="120" y1="100" x2="392" y2="260" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor={AIR} />
          <stop offset="100%" stopColor="#818CF8" stopOpacity="0.85" />
        </linearGradient>
        <linearGradient id={id("soil")} x1="100" y1="256" x2="412" y2="360" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor={SOIL} />
          <stop offset="100%" stopColor="#10B981" stopOpacity="0.9" />
        </linearGradient>
        <linearGradient id={id("water")} x1="120" y1="330" x2="392" y2="430" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0284C7" />
          <stop offset="100%" stopColor="#2563EB" />
        </linearGradient>
      </defs>
      <rect x="24" y="24" width="464" height="464" rx="108" fill={`url(#${id("bg")})`} />
      <circle cx="256" cy="256" r="168" stroke="#94A3B8" strokeOpacity="0.12" strokeWidth="2" strokeDasharray="6 8" />
      <circle cx="256" cy="256" r="118" stroke="#94A3B8" strokeOpacity="0.18" strokeWidth="1.5" />
      <path d="M136 220 C166 132, 346 132, 376 220 C336 184, 176 184, 136 220 Z" fill={`url(#${id("air")})`} />
      <path
        d="M116 286 C176 248, 336 248, 396 286 C356 324, 156 324, 116 286 Z"
        fill={`url(#${id("soil")})`}
        opacity="0.92"
      />
      <path d="M140 342 C192 382, 320 382, 372 342 C340 412, 172 412, 140 342 Z" fill={`url(#${id("water")})`} />
      <polygon
        points="256,172 328,214 328,298 256,340 184,298 184,214"
        fill={INK}
        fillOpacity="0.78"
        stroke={RIM}
        strokeWidth="10"
        strokeLinejoin="round"
      />
      <line x1="256" y1="256" x2="256" y2="178" stroke={AIR} strokeWidth="6" strokeLinecap="round" />
      <line x1="256" y1="256" x2="322" y2="294" stroke={SOIL} strokeWidth="6" strokeLinecap="round" />
      <line x1="256" y1="256" x2="190" y2="294" stroke="#60A5FA" strokeWidth="6" strokeLinecap="round" />
      <circle cx="256" cy="256" r="18" fill="#FFFFFF" />
      <circle cx="256" cy="256" r="8" fill={AIR} />
    </>
  );
}

/**
 * The EcoFate squircle mark, inline so it scales crisply and glows on hover (inside a `group`).
 * Decorative: the wordmark beside it, or the caller, names the app.
 */
export function BrandMark({ size = 32 }: { size?: number }) {
  // Gradient ids must be unique per instance and valid inside `url(#...)`.
  const prefix = `brand${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const detailed = size >= DETAIL_MIN_PX;
  return (
    <svg
      aria-hidden="true"
      viewBox={detailed ? "0 0 512 512" : "0 0 64 64"}
      width={size}
      height={size}
      fill="none"
      className={`shrink-0 ${GLOW}`}
    >
      {detailed ? <DetailedMark prefix={prefix} /> : <SimpleMark />}
    </svg>
  );
}

const COMPARTMENTS = [
  { name: "Air", note: "Air: atmospheric releases and dispersion (available)", active: true },
  { name: "Water", note: "Surface water: a planned compartment, not yet available", active: false },
  { name: "Soil", note: "Soil and subsurface: a planned compartment, not yet available", active: false },
];

/** The environmental compartments: air is active, water and soil are upcoming modules. */
export function CompartmentPill() {
  return (
    <ul
      aria-label="Compartments"
      className="inline-flex items-center gap-1.5 rounded-full border border-hairline px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider"
    >
      {COMPARTMENTS.map(({ name, note, active }, index) => (
        <li key={name} title={note} className="flex items-center gap-1.5">
          {index > 0 ? (
            <span aria-hidden="true" className="text-fg2">
              •
            </span>
          ) : null}
          <span className={active ? "text-accent" : "text-fg2 opacity-60"}>{name}</span>
          <span className="sr-only">{active ? "(available)" : "(planned)"}</span>
        </li>
      ))}
    </ul>
  );
}

interface BrandLogoProps {
  /** Mark size, px. */
  size?: number;
  /** A micro-label under the wordmark (for example in the navigation rail). */
  label?: string | undefined;
  /** Shows the compartment pill under the wordmark. */
  compartments?: boolean;
}

/** The mark beside the "EcoFate" wordmark, with an optional micro-label or compartment pill. */
export function BrandLogo({ size = 32, label, compartments = false }: BrandLogoProps) {
  return (
    <span className="group flex min-w-0 items-center gap-2.5">
      <BrandMark size={size} />
      <span className="flex min-w-0 flex-col items-start gap-0.5">
        <span className={`truncate font-semibold tracking-tight ${size >= DETAIL_MIN_PX ? "text-xl" : "text-sm"}`}>
          EcoFate
        </span>
        {label ? (
          <span className="truncate text-[10px] font-medium uppercase tracking-wider text-fg2">{label}</span>
        ) : null}
        {compartments ? <CompartmentPill /> : null}
      </span>
    </span>
  );
}
