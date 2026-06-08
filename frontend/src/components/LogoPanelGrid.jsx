export default function LogoPanelGrid({ size = 36 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="lpg-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#00d4ff" />
          <stop offset="100%" stopColor="#7c6af7" />
        </linearGradient>
        <filter id="lpg-glow">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="lpg-softglow">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Background */}
      <rect width="100" height="100" rx="18" fill="#111828" />

      {/* Soft glow behind centre cell */}
      <rect x="37" y="37" width="26" height="26" rx="5"
        fill="#00d4ff" opacity="0.15" filter="url(#lpg-softglow)" />

      {/* ── 3×3 grid ── */}
      {/* Row 1 */}
      <rect x="8"  y="8"  width="24" height="24" rx="4" fill="#1e2a40" />
      <rect x="38" y="8"  width="24" height="24" rx="4" fill="#1e2a40" />
      <rect x="68" y="8"  width="24" height="24" rx="4" fill="#1e2a40" />

      {/* Row 2 — side cells */}
      <rect x="8"  y="38" width="24" height="24" rx="4" fill="#1e2a40" />
      {/* Centre cell — gradient + glow */}
      <rect x="38" y="38" width="24" height="24" rx="5"
        fill="url(#lpg-grad)" filter="url(#lpg-glow)" />
      <rect x="68" y="38" width="24" height="24" rx="4" fill="#1e2a40" />

      {/* Row 3 */}
      <rect x="8"  y="68" width="24" height="24" rx="4" fill="#1e2a40" />
      <rect x="38" y="68" width="24" height="24" rx="4" fill="#1e2a40" />
      <rect x="68" y="68" width="24" height="24" rx="4" fill="#1e2a40" />

      {/* Neural node inside centre cell */}
      <circle cx="50" cy="50" r="5.5" fill="#0a0d14" />
      <line x1="50" y1="40" x2="50" y2="44.5" stroke="#0a0d14" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="50" y1="55.5" x2="50" y2="60" stroke="#0a0d14" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="40" y1="50" x2="44.5" y2="50" stroke="#0a0d14" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="55.5" y1="50" x2="60" y2="50" stroke="#0a0d14" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="50" cy="50" r="2.2" fill="#0a0d14" />

      {/* Dashed connection lines to adjacent cells */}
      <line x1="50" y1="38" x2="50" y2="32"
        stroke="#00d4ff" strokeWidth="1.2" strokeDasharray="2,2" opacity="0.6" />
      <line x1="50" y1="62" x2="50" y2="68"
        stroke="#7c6af7" strokeWidth="1.2" strokeDasharray="2,2" opacity="0.6" />
      <line x1="38" y1="50" x2="32" y2="50"
        stroke="#00d4ff" strokeWidth="1.2" strokeDasharray="2,2" opacity="0.6" />
      <line x1="62" y1="50" x2="68" y2="50"
        stroke="#7c6af7" strokeWidth="1.2" strokeDasharray="2,2" opacity="0.6" />
    </svg>
  );
}
