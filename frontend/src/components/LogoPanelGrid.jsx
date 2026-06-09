export default function LogoPanelGrid({ size = 36 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="55 55 290 220"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="lpg-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#00d4ff" />
          <stop offset="100%" stopColor="#7c6af7" />
        </linearGradient>
        <filter id="lpg-glow8c">
          <feGaussianBlur stdDeviation="6" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="lpg-glow8s">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Connection lines — centre to outer nodes */}
      <g stroke="#1e2a40" strokeWidth="1.5" opacity="0.8">
        <line x1="200" y1="175" x2="200" y2="92" />
        <line x1="200" y1="175" x2="275" y2="120" />
        <line x1="200" y1="175" x2="308" y2="196" />
        <line x1="200" y1="175" x2="272" y2="248" />
        <line x1="200" y1="175" x2="128" y2="248" />
        <line x1="200" y1="175" x2="92"  y2="196" />
        <line x1="200" y1="175" x2="125" y2="120" />
      </g>

      {/* Outer-to-outer dashed connections */}
      <g stroke="#1e2a40" strokeWidth="1" opacity="0.4" strokeDasharray="4,3">
        <line x1="200" y1="92"  x2="275" y2="120" />
        <line x1="275" y1="120" x2="308" y2="196" />
        <line x1="308" y1="196" x2="272" y2="248" />
        <line x1="272" y1="248" x2="128" y2="248" />
        <line x1="128" y1="248" x2="92"  y2="196" />
        <line x1="92"  y1="196" x2="125" y2="120" />
        <line x1="125" y1="120" x2="200" y2="92"  />
      </g>

      {/* Glowing accent lines */}
      <line x1="200" y1="175" x2="275" y2="120" stroke="url(#lpg-grad)" strokeWidth="2" opacity="0.5" />
      <line x1="200" y1="175" x2="308" y2="196" stroke="#00d4ff" strokeWidth="2" opacity="0.4" />
      <line x1="200" y1="175" x2="200" y2="92"  stroke="#7c6af7" strokeWidth="2" opacity="0.4" />

      {/* Outer nodes */}
      <g filter="url(#lpg-glow8s)">
        <circle cx="200" cy="92"  r="9" fill="#7c6af7" opacity="0.85" />
        <circle cx="275" cy="120" r="9" fill="#00d4ff" opacity="0.85" />
        <circle cx="308" cy="196" r="9" fill="#00d4ff" opacity="0.7" />
        <circle cx="272" cy="248" r="9" fill="#7c6af7" opacity="0.7" />
        <circle cx="128" cy="248" r="9" fill="#7c6af7" opacity="0.7" />
        <circle cx="92"  cy="196" r="9" fill="#00d4ff" opacity="0.7" />
        <circle cx="125" cy="120" r="9" fill="#7c6af7" opacity="0.85" />
      </g>

      {/* Inner dots on outer nodes */}
      <g fill="#0a0d14">
        <circle cx="200" cy="92"  r="4" />
        <circle cx="275" cy="120" r="4" />
        <circle cx="308" cy="196" r="4" />
        <circle cx="272" cy="248" r="4" />
        <circle cx="128" cy="248" r="4" />
        <circle cx="92"  cy="196" r="4" />
        <circle cx="125" cy="120" r="4" />
      </g>

      {/* Central node */}
      <circle cx="200" cy="175" r="28" fill="url(#lpg-grad)" filter="url(#lpg-glow8c)" />
      <circle cx="200" cy="175" r="18" fill="#0a0d14" />

      {/* Mini panel grid inside centre node */}
      <g transform="translate(189, 164)">
        <rect x="0"  y="0"  width="6" height="6" rx="1" fill="#1e2a40" />
        <rect x="8"  y="0"  width="6" height="6" rx="1" fill="#1e2a40" />
        <rect x="16" y="0"  width="6" height="6" rx="1" fill="#1e2a40" />
        <rect x="0"  y="8"  width="6" height="6" rx="1" fill="#1e2a40" />
        <rect x="8"  y="8"  width="6" height="6" rx="1" fill="url(#lpg-grad)" />
        <rect x="16" y="8"  width="6" height="6" rx="1" fill="#1e2a40" />
        <rect x="0"  y="16" width="6" height="6" rx="1" fill="#1e2a40" />
        <rect x="8"  y="16" width="6" height="6" rx="1" fill="#1e2a40" />
        <rect x="16" y="16" width="6" height="6" rx="1" fill="#1e2a40" />
      </g>
    </svg>
  );
}
