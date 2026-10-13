// Hand-drawn SVG fan-art versions of the Bikini Bottom crew. Pure code, no images.

type Props = { size?: number; className?: string; title?: string }

const svgProps = (size: number, title?: string) => ({
  width: size,
  height: size,
  viewBox: '0 0 120 120',
  role: title ? 'img' : undefined,
  'aria-label': title,
  'aria-hidden': title ? undefined : true,
})

const Eye = ({ x, y, r = 9, pupil = '#1d6fb8', look = 1 }: { x: number; y: number; r?: number; pupil?: string; look?: number }) => (
  <g>
    <circle cx={x} cy={y} r={r} fill="#fff" stroke="#1a1a1a" strokeWidth="1.6" />
    <circle cx={x + look} cy={y + 1} r={r * 0.48} fill={pupil} />
    <circle cx={x + look} cy={y + 1} r={r * 0.24} fill="#111" />
    <circle cx={x + look - r * 0.2} cy={y - r * 0.1} r={r * 0.12} fill="#fff" />
  </g>
)

export function MrKrabs({ size = 96, className, title }: Props) {
  return (
    <svg {...svgProps(size, title)} className={className}>
      {/* eye stalks */}
      <rect x="44" y="10" width="7" height="34" rx="3.5" fill="#d93a2b" stroke="#7a1a12" strokeWidth="1.4" />
      <rect x="69" y="10" width="7" height="34" rx="3.5" fill="#d93a2b" stroke="#7a1a12" strokeWidth="1.4" />
      <Eye x={47.5} y={12} r={9} pupil="#6b3d1a" />
      <Eye x={72.5} y={12} r={9} pupil="#6b3d1a" look={-1} />
      {/* claws */}
      <g stroke="#7a1a12" strokeWidth="1.6">
        <path d="M18 70 q-14 -14 -4 -30 q10 4 12 14 q8 -10 16 -4 q-6 14 -24 20z" fill="#e2452f" />
        <path d="M102 70 q14 -14 4 -30 q-10 4 -12 14 q-8 -10 -16 -4 q6 14 24 20z" fill="#e2452f" />
        <path d="M26 72 l12 6" fill="none" strokeWidth="5" stroke="#e2452f" />
        <path d="M94 72 l-12 6" fill="none" strokeWidth="5" stroke="#e2452f" />
      </g>
      {/* body */}
      <ellipse cx="60" cy="72" rx="32" ry="30" fill="#e2452f" stroke="#7a1a12" strokeWidth="1.8" />
      {/* shirt */}
      <path d="M30 84 q30 22 60 0 l-2 14 q-28 16 -56 0z" fill="#4a90d9" stroke="#1d4f86" strokeWidth="1.4" />
      <rect x="31" y="86" width="58" height="5" fill="#7a4a1d" />
      {/* face */}
      <path d="M44 60 q16 -8 32 0" stroke="#7a1a12" strokeWidth="2" fill="none" />
      <path d="M46 72 q14 12 28 0" stroke="#5a0f0a" strokeWidth="2.4" fill="#5a0f0a" />
      <path d="M52 73 l2 5 l3 -5 M62 73 l2 5 l3 -5" fill="#fff" stroke="none" />
      {/* legs */}
      <path d="M48 102 l-4 14 M72 102 l4 14" stroke="#d93a2b" strokeWidth="5" strokeLinecap="round" />
    </svg>
  )
}

export function SpongeBob({ size = 96, className, title }: Props) {
  return (
    <svg {...svgProps(size, title)} className={className}>
      <rect x="22" y="10" width="76" height="70" rx="8" fill="#fff35b" stroke="#a69a12" strokeWidth="2" />
      {/* sponge holes */}
      {[
        [32, 20, 4], [86, 24, 5], [30, 62, 5], [88, 66, 4], [56, 70, 3], [80, 46, 3], [34, 42, 3],
      ].map(([x, y, r], i) => (
        <circle key={i} cx={x} cy={y} r={r} fill="#c9bb20" opacity=".75" />
      ))}
      <Eye x={48} y={36} r={11} />
      <Eye x={72} y={36} r={11} look={-1} />
      <path d="M40 23 l-2 -5 M46 22 l0 -6 M52 23 l2 -5 M66 23 l-2 -5 M72 22 l0 -6 M78 23 l2 -5" stroke="#111" strokeWidth="1.6" />
      <ellipse cx="60" cy="48" rx="4" ry="6" fill="#f1e23a" stroke="#a69a12" />
      <circle cx="36" cy="54" r="5" fill="#ff9a8b" opacity=".7" />
      <circle cx="84" cy="54" r="5" fill="#ff9a8b" opacity=".7" />
      <path d="M38 54 q22 22 44 0" stroke="#7a1a12" strokeWidth="2.2" fill="#7a1a12" />
      <rect x="51" y="54" width="7" height="8" fill="#fff" stroke="#999" strokeWidth=".6" />
      <rect x="61" y="54" width="7" height="8" fill="#fff" stroke="#999" strokeWidth=".6" />
      {/* shirt + tie */}
      <rect x="22" y="78" width="76" height="8" fill="#fff" stroke="#a69a12" strokeWidth="1.2" />
      <path d="M56 78 l4 4 l4 -4 l-2 12 l-2 3 l-2 -3z" fill="#e2302b" />
      {/* shorts */}
      <rect x="22" y="86" width="76" height="14" fill="#9b5b22" stroke="#5c3510" strokeWidth="1.4" />
      <rect x="22" y="89" width="76" height="3" fill="#2d2d2d" />
      <path d="M40 100 v14 M80 100 v14" stroke="#fff35b" strokeWidth="5" strokeLinecap="round" />
      <ellipse cx="38" cy="115" rx="7" ry="3.5" fill="#111" />
      <ellipse cx="82" cy="115" rx="7" ry="3.5" fill="#111" />
    </svg>
  )
}

export function Squidward({ size = 96, className, title }: Props) {
  return (
    <svg {...svgProps(size, title)} className={className}>
      <path d="M38 50 q-6 -42 22 -44 q28 2 22 44z" fill="#9fd3c7" stroke="#3e7b6e" strokeWidth="2" />
      {/* droopy eyes */}
      <ellipse cx="49" cy="40" rx="9" ry="10" fill="#fffbe6" stroke="#3e7b6e" strokeWidth="1.6" />
      <ellipse cx="71" cy="40" rx="9" ry="10" fill="#fffbe6" stroke="#3e7b6e" strokeWidth="1.6" />
      <circle cx="49" cy="43" r="3.6" fill="#c0392b" />
      <circle cx="71" cy="43" r="3.6" fill="#c0392b" />
      <path d="M40 38 q9 -6 18 0 v-6 q-9 -6 -18 0z" fill="#9fd3c7" stroke="#3e7b6e" strokeWidth="1.4" />
      <path d="M62 38 q9 -6 18 0 v-6 q-9 -6 -18 0z" fill="#9fd3c7" stroke="#3e7b6e" strokeWidth="1.4" />
      {/* long nose */}
      <path d="M56 46 q-2 26 4 34 q6 -8 4 -34z" fill="#8cc6b9" stroke="#3e7b6e" strokeWidth="1.6" />
      <path d="M48 70 q12 -4 24 0" stroke="#3e7b6e" strokeWidth="2" fill="none" />
      {/* shirt */}
      <path d="M40 76 h40 l6 26 h-52z" fill="#a0612b" stroke="#5c3510" strokeWidth="1.6" />
      {/* tentacles */}
      <path d="M40 102 q-6 10 -12 12 M52 102 q-2 10 -6 14 M68 102 q2 10 6 14 M80 102 q6 10 12 12" stroke="#9fd3c7" strokeWidth="6" fill="none" strokeLinecap="round" />
    </svg>
  )
}

export function Patrick({ size = 96, className, title }: Props) {
  return (
    <svg {...svgProps(size, title)} className={className}>
      <path
        d="M60 6 L72 46 L112 52 L80 74 L92 114 L60 90 L28 114 L40 74 L8 52 L48 46 Z"
        fill="#ff9fb3" stroke="#c14d6c" strokeWidth="2.2" strokeLinejoin="round"
      />
      {/* shorts */}
      <path d="M33 82 L87 82 L90 96 L60 90 L30 96 Z" fill="#9be15d" stroke="#4c8a23" strokeWidth="1.6" />
      <circle cx="44" cy="88" r="2.6" fill="#b06ad9" />
      <circle cx="72" cy="87" r="2.6" fill="#b06ad9" />
      <circle cx="58" cy="85" r="2" fill="#b06ad9" />
      <Eye x={53} y={38} r={7} pupil="#111" look={0.5} />
      <Eye x={67} y={38} r={7} pupil="#111" look={-0.5} />
      <path d="M46 28 q6 -4 12 0 M62 28 q6 -4 12 0" stroke="#111" strokeWidth="2" fill="none" />
      <path d="M48 56 q12 12 24 0" stroke="#7a1a12" strokeWidth="2.4" fill="#7a1a12" />
    </svg>
  )
}

export function Sandy({ size = 96, className, title }: Props) {
  return (
    <svg {...svgProps(size, title)} className={className}>
      {/* suit */}
      <path d="M32 80 q28 -12 56 0 l6 34 h-68z" fill="#f4f4f4" stroke="#9aa5ad" strokeWidth="1.6" />
      <rect x="54" y="84" width="12" height="10" rx="2" fill="#7fb2d6" />
      {/* face */}
      <ellipse cx="60" cy="54" rx="26" ry="24" fill="#a8693a" stroke="#5c3510" strokeWidth="1.6" />
      <ellipse cx="60" cy="62" rx="16" ry="12" fill="#e9c9a1" />
      <Eye x={50} y={48} r={7} pupil="#4a2a10" />
      <Eye x={70} y={48} r={7} pupil="#4a2a10" look={-0.5} />
      <ellipse cx="60" cy="58" rx="4" ry="3" fill="#3a1d08" />
      <path d="M52 64 q8 8 16 0" stroke="#5c3510" strokeWidth="2" fill="none" />
      <rect x="56" y="65" width="8" height="6" fill="#fff" stroke="#999" strokeWidth=".5" />
      {/* air helmet */}
      <circle cx="60" cy="52" r="40" fill="#cfefff" fillOpacity=".25" stroke="#b9e6ff" strokeWidth="2.5" />
      <path d="M30 34 q8 -16 26 -20" stroke="#fff" strokeWidth="4" fill="none" strokeLinecap="round" opacity=".8" />
      {/* flower */}
      <g transform="translate(86 16)">
        {[0, 72, 144, 216, 288].map((r) => (
          <ellipse key={r} cx="0" cy="-6" rx="4" ry="6" fill="#ff7eb6" transform={`rotate(${r})`} />
        ))}
        <circle r="3.5" fill="#ffd23f" />
      </g>
    </svg>
  )
}

export function Plankton({ size = 64, className, title }: Props) {
  return (
    <svg {...svgProps(size, title)} className={className}>
      <path d="M50 22 q-10 -14 -18 -16 M70 22 q10 -14 18 -16" stroke="#2f7a2a" strokeWidth="3" fill="none" strokeLinecap="round" />
      <ellipse cx="60" cy="60" rx="24" ry="36" fill="#5fbf3c" stroke="#2f7a2a" strokeWidth="2.2" />
      <ellipse cx="60" cy="48" rx="15" ry="13" fill="#fff6c4" stroke="#2f7a2a" strokeWidth="1.6" />
      <circle cx="60" cy="49" r="7" fill="#d62828" />
      <circle cx="60" cy="49" r="3.4" fill="#111" />
      <circle cx="57" cy="46" r="1.6" fill="#fff" />
      <path d="M43 32 l34 8" stroke="#1d4d1a" strokeWidth="4" strokeLinecap="round" />
      <path d="M50 76 q10 -6 20 0" stroke="#1d4d1a" strokeWidth="2.4" fill="none" />
      <path d="M38 64 l-14 8 M82 64 l14 8" stroke="#5fbf3c" strokeWidth="4" strokeLinecap="round" />
      <path d="M52 94 l-4 16 M68 94 l4 16" stroke="#5fbf3c" strokeWidth="4" strokeLinecap="round" />
    </svg>
  )
}

export function Gary({ size = 96, className, title }: Props) {
  return (
    <svg {...svgProps(size, title)} className={className} viewBox="0 0 140 120">
      {/* body */}
      <path d="M10 100 q0 -18 30 -20 h70 q20 2 22 20z" fill="#7fc8e8" stroke="#2e7ea5" strokeWidth="2" />
      {/* eye stalks */}
      <path d="M118 82 q2 -26 -2 -40 M126 84 q6 -24 6 -38" stroke="#7fc8e8" strokeWidth="5" fill="none" strokeLinecap="round" />
      <ellipse cx="115" cy="38" rx="7" ry="8" fill="#fffbe6" stroke="#2e7ea5" strokeWidth="1.4" />
      <ellipse cx="132" cy="42" rx="7" ry="8" fill="#fffbe6" stroke="#2e7ea5" strokeWidth="1.4" />
      <circle cx="116" cy="40" r="3.2" fill="#c0392b" />
      <circle cx="133" cy="44" r="3.2" fill="#c0392b" />
      <path d="M118 94 q6 4 10 0" stroke="#2e7ea5" strokeWidth="2" fill="none" />
      {/* shell */}
      <circle cx="62" cy="58" r="34" fill="#ff8fa3" stroke="#b33f5c" strokeWidth="2.2" />
      <path d="M62 58 m0 -6 a6 6 0 1 1 -6 6 a12 12 0 1 1 12 12 a18 18 0 1 1 -18 -18 a24 24 0 1 1 24 24"
        stroke="#3f2a7a" strokeWidth="3" fill="none" strokeLinecap="round" />
      <path d="M40 34 q10 -10 24 -10" stroke="#ffd1db" strokeWidth="4" fill="none" strokeLinecap="round" />
    </svg>
  )
}
