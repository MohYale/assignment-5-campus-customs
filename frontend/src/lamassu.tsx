import type { ReactNode } from 'react'

const SKIN = '#5f9e3a'
const SKIN_DARK = '#3d7324'
const PLASTRON = '#f3d7a2'
const SHELL = '#6b4423'

type Weapon = 'swords' | 'staff' | 'sai' | 'nunchucks'

function Turtle({ mask, weapon }: { mask: string; weapon: Weapon }): ReactNode {
  return (
    <>
      {weapon === 'swords' ? (
        <>
          <path d="M72 100 L52 24" stroke="#e6ebf0" strokeWidth="4" strokeLinecap="round" />
          <path d="M148 100 L168 24" stroke="#e6ebf0" strokeWidth="4" strokeLinecap="round" />
          <rect x="64" y="96" width="16" height="7" rx="1" fill={mask} />
          <rect x="140" y="96" width="16" height="7" rx="1" fill={mask} />
        </>
      ) : null}
      {weapon === 'staff' ? <path d="M168 18 L156 152" stroke="#6b4a2a" strokeWidth="5" strokeLinecap="round" /> : null}
      {weapon === 'sai' ? (
        <>
          <path d="M48 108 V78" stroke="#c5ccd4" strokeWidth="3" strokeLinecap="round" />
          <path d="M42 88 L54 88" stroke="#c5ccd4" strokeWidth="3" strokeLinecap="round" />
          <path d="M172 108 V78" stroke="#c5ccd4" strokeWidth="3" strokeLinecap="round" />
          <path d="M166 88 L178 88" stroke="#c5ccd4" strokeWidth="3" strokeLinecap="round" />
          <rect x="44" y="104" width="8" height="10" fill={mask} />
          <rect x="168" y="104" width="8" height="10" fill={mask} />
        </>
      ) : null}
      {weapon === 'nunchucks' ? (
        <>
          <circle cx="46" cy="96" r="7" fill="#d8a15a" stroke="#6b4a2a" strokeWidth="1.5" />
          <circle cx="46" cy="118" r="7" fill="#d8a15a" stroke="#6b4a2a" strokeWidth="1.5" />
          <path d="M46 103 V111" stroke="#6b4a2a" strokeWidth="2" />
        </>
      ) : null}
      <ellipse cx="110" cy="118" rx="54" ry="38" fill={SHELL} stroke="#3d2916" strokeWidth="2" />
      <path d="M68 112 Q110 86 152 112" fill="none" stroke="#3d2916" strokeWidth="2" />
      <path d="M86 128 Q110 112 134 128" fill="none" stroke="#3d2916" strokeWidth="1.6" />
      <ellipse cx="76" cy="146" rx="16" ry="11" fill={SKIN} stroke={SKIN_DARK} strokeWidth="1.4" />
      <ellipse cx="144" cy="146" rx="16" ry="11" fill={SKIN} stroke={SKIN_DARK} strokeWidth="1.4" />
      <ellipse cx="58" cy="112" rx="15" ry="11" fill={SKIN} stroke={SKIN_DARK} strokeWidth="1.4" />
      <ellipse cx="162" cy="112" rx="15" ry="11" fill={SKIN} stroke={SKIN_DARK} strokeWidth="1.4" />
      <ellipse cx="110" cy="120" rx="30" ry="26" fill={PLASTRON} stroke="#c4a36a" strokeWidth="1.4" />
      <rect x="84" y="108" width="52" height="8" rx="2" fill={mask} />
      <ellipse cx="110" cy="62" rx="30" ry="25" fill={SKIN} stroke={SKIN_DARK} strokeWidth="1.6" />
      <path d="M80 56 Q110 48 140 56 Q140 70 110 74 Q80 70 80 56 Z" fill={mask} />
      <path d="M80 58 L58 46 L66 72 Z" fill={mask} />
      <path d="M140 58 L162 46 L154 72 Z" fill={mask} />
      <ellipse cx="98" cy="60" rx="7" ry="8" fill="#fffaf1" />
      <ellipse cx="122" cy="60" rx="7" ry="8" fill="#fffaf1" />
      <circle cx="100" cy="61" r="3" fill="#1c1915" />
      <circle cx="124" cy="61" r="3" fill="#1c1915" />
      <path d="M100 74 Q110 82 120 74" fill="none" stroke={SKIN_DARK} strokeWidth="1.6" strokeLinecap="round" />
    </>
  )
}

function Splinter(): ReactNode {
  return (
    <>
      <path d="M64 128 C28 150 24 108 58 112" fill="none" stroke="#8d7056" strokeWidth="7" strokeLinecap="round" />
      <path d="M176 28 L164 150" stroke="#6b4a2a" strokeWidth="6" strokeLinecap="round" />
      <path d="M68 92 Q110 76 156 92 L168 150 H56 Z" fill="#7a3340" stroke="#4e222b" strokeWidth="1.6" />
      <path d="M96 96 V146" stroke="#f0d48a" strokeWidth="2" />
      <ellipse cx="78" cy="34" rx="16" ry="24" fill="#b08968" stroke="#6e5340" strokeWidth="1.5" />
      <ellipse cx="146" cy="34" rx="16" ry="24" fill="#b08968" stroke="#6e5340" strokeWidth="1.5" />
      <ellipse cx="78" cy="36" rx="8" ry="14" fill="#e8b7ae" />
      <ellipse cx="146" cy="36" rx="8" ry="14" fill="#e8b7ae" />
      <ellipse cx="112" cy="66" rx="34" ry="30" fill="#b08968" stroke="#6e5340" strokeWidth="1.6" />
      <ellipse cx="112" cy="80" rx="14" ry="9" fill="#d7b89a" />
      <ellipse cx="106" cy="78" rx="2" ry="2.4" fill="#3d2916" />
      <ellipse cx="118" cy="78" rx="2" ry="2.4" fill="#3d2916" />
      <path d="M90 86 Q112 112 134 86 Q112 100 90 86 Z" fill="#f7f1e6" />
      <ellipse cx="98" cy="62" rx="6" ry="4.5" fill="#fffaf1" />
      <ellipse cx="126" cy="62" rx="6" ry="4.5" fill="#fffaf1" />
      <circle cx="99" cy="62" r="2.1" fill="#1c1915" />
      <circle cx="127" cy="62" r="2.1" fill="#1c1915" />
      <path d="M78 74 H98 M76 80 H98 M126 74 H148 M126 80 H150" stroke="#6e5340" strokeWidth="1.2" />
      <ellipse cx="62" cy="118" rx="11" ry="8" fill="#b08968" stroke="#6e5340" />
      <ellipse cx="168" cy="116" rx="10" ry="7" fill="#b08968" stroke="#6e5340" />
      <ellipse cx="90" cy="150" rx="16" ry="8" fill="#b08968" stroke="#6e5340" />
      <ellipse cx="136" cy="150" rx="16" ry="8" fill="#b08968" stroke="#6e5340" />
    </>
  )
}

const SPECIALISTS = [
  { id: 'inventory', name: 'Leonardo', note: 'Inventory', mask: '#1f4fbf', weapon: 'swords' as const },
  { id: 'accounting', name: 'Donatello', note: 'Accounting', mask: '#6b3fa0', weapon: 'staff' as const },
  { id: 'facilities', name: 'Raphael', note: 'Facilities', mask: '#b4232a', weapon: 'sai' as const },
  { id: 'customer_service', name: 'Michelangelo', note: 'Customer service', mask: '#e07a1f', weapon: 'nunchucks' as const },
]

type Spot = { x: number; y: number; scale: number; cx: number; top: number; bottom: number }

function spot(x: number, y: number, scale: number): Spot {
  return {
    x,
    y,
    scale,
    cx: x + (220 * scale) / 2,
    top: y,
    bottom: y + 160 * scale,
  }
}

const bossSpot = spot(378, 46, 1)
const childSpots = SPECIALISTS.map((agent, index) => ({
  ...agent,
  ...spot(28 + index * 240, 328, 0.74),
}))

type Props = {
  activeAgent: string | null
  litAgents: string[]
  edges: { from: string; to: string }[]
  latest: { from: string; to: string } | null
}

export function LamassuYard({ activeAgent, litAgents, edges, latest }: Props) {
  return (
    <svg className="yard" viewBox="0 0 980 530" role="img" aria-label="Splinter above Leonardo, Donatello, Raphael, and Michelangelo">
      {childSpots.map((child) => {
        const used = edges.some(
          (edge) =>
            (edge.from === 'boss' && edge.to === child.id) ||
            (edge.from === child.id && edge.to === 'boss'),
        )
        const hot =
          latest !== null &&
          ((latest.from === 'boss' && latest.to === child.id) ||
            (latest.from === child.id && latest.to === 'boss'))
        return (
          <line
            key={child.id}
            x1={bossSpot.cx}
            y1={bossSpot.bottom - 6}
            x2={child.cx}
            y2={child.top + 4}
            className={hot ? 'wire hot' : used ? 'wire used' : 'wire'}
          />
        )
      })}
      <Figure
        name="Splinter"
        note="Boss"
        place={bossSpot}
        speaking={activeAgent === 'boss'}
        lit={litAgents.includes('boss')}
      >
        <Splinter />
      </Figure>
      {childSpots.map((child) => (
        <Figure
          key={child.id}
          name={child.name}
          note={child.note}
          place={child}
          speaking={activeAgent === child.id}
          lit={litAgents.includes(child.id)}
        >
          <Turtle mask={child.mask} weapon={child.weapon} />
        </Figure>
      ))}
      <desc>
        Splinter stands at the top. Lines run down to Leonardo, Donatello, Raphael, and Michelangelo.
        A lit line is a handoff already taken. The highlighted turtle is the agent speaking now.
      </desc>
    </svg>
  )
}

function Figure({
  name,
  note,
  place,
  speaking,
  lit,
  children,
}: {
  name: string
  note: string
  place: Spot
  speaking: boolean
  lit: boolean
  children: ReactNode
}) {
  const ring = speaking ? '#00356b' : lit ? '#a0792c' : 'none'
  return (
    <g className={speaking ? 'figure-node speaking' : 'figure-node'} transform={`translate(${place.x} ${place.y}) scale(${place.scale})`}>
      {ring !== 'none' ? (
        <ellipse cx="110" cy="96" rx="86" ry="74" fill="none" stroke={ring} strokeWidth={speaking ? 4 : 2.5} />
      ) : null}
      {name === 'Splinter' ? (
        <>
          <text x="110" y="-22" textAnchor="middle" className="figure-name" fontSize="22">
            {name}
          </text>
          <text x="110" y="-4" textAnchor="middle" className="figure-note" fontSize="14">
            {note}
          </text>
        </>
      ) : null}
      {children}
      {name === 'Splinter' ? null : (
        <>
          <text x="110" y="176" textAnchor="middle" className="figure-name" fontSize="16">
            {name}
          </text>
          <text x="110" y="194" textAnchor="middle" className="figure-note" fontSize="13">
            {note}
          </text>
        </>
      )}
    </g>
  )
}

export function agentLabel(agent: string | null): string {
  if (agent === 'boss') return 'Splinter'
  if (agent === 'inventory') return 'Leonardo'
  if (agent === 'accounting') return 'Donatello'
  if (agent === 'facilities') return 'Raphael'
  if (agent === 'customer_service') return 'Michelangelo'
  return agent ?? 'The desk'
}
