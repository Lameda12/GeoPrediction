'use client';

import { motion } from 'framer-motion';
import type { EscalationNode } from '@/lib/types';

interface Props { nodes: EscalationNode[] }

// Two-branch layout: escalation (left) and de-escalation (right)
const POSITIONS: Record<number, { x: number; y: number }> = {
  1: { x: 50,  y: 12  },  // Initial Strike (top center)
  2: { x: 50,  y: 26  },  // Iran Retaliation
  3: { x: 50,  y: 40  },  // Proxy Activation
  4: { x: 22,  y: 56  },  // Escalation Decision (left branch)
  5: { x: 78,  y: 56  },  // De-escalation Window (right branch)
  6: { x: 78,  y: 70  },  // Ceasefire
  7: { x: 22,  y: 70  },  // Nuclear Signaling
  8: { x: 22,  y: 86  },  // Threshold Breach
};

// Edges: [from, to]
const EDGES: [number, number][] = [
  [1, 2], [2, 3], [3, 4], [3, 5], [4, 7], [5, 6], [7, 8],
];

export default function EscalationGraph({ nodes }: Props) {
  const byId = Object.fromEntries(nodes.map(n => [n.id, n]));

  return (
    <div className="w-full h-full relative select-none">
      <svg
        viewBox="0 0 100 100"
        className="w-full h-full"
        style={{ overflow: 'visible' }}
      >
        {/* Background grid */}
        <defs>
          <pattern id="grid" width="5" height="5" patternUnits="userSpaceOnUse">
            <path d="M5,0 L0,0 0,5" fill="none" stroke="rgba(14,45,74,0.5)" strokeWidth="0.2" />
          </pattern>
          <filter id="glow">
            <feGaussianBlur stdDeviation="0.8" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <rect width="100" height="100" fill="url(#grid)" />

        {/* Edges */}
        {EDGES.map(([fId, tId]) => {
          const f = POSITIONS[fId];
          const t = POSITIONS[tId];
          const fn = byId[fId];
          const tn = byId[tId];
          if (!f || !t || !fn || !tn) return null;
          const active = fn.active && tn.active;
          const isEscalation = tId === 4 || tId === 7 || tId === 8;
          const color = active
            ? (isEscalation ? '#ff4400' : '#00aa44')
            : '#0e2d4a';

          return (
            <g key={`e${fId}-${tId}`}>
              <line
                x1={f.x} y1={f.y + 2}
                x2={t.x} y2={t.y - 2}
                stroke={color}
                strokeWidth={active ? 0.6 : 0.4}
                strokeDasharray={active ? '2,1' : '1,2'}
                opacity={active ? 0.9 : 0.35}
                filter={active ? 'url(#glow)' : undefined}
              />
              {/* Arrowhead */}
              <circle
                cx={t.x + (f.x - t.x) * 0.15}
                cy={t.y + (f.y - t.y) * 0.15}
                r="0.5"
                fill={color}
                opacity={active ? 0.8 : 0.3}
              />
            </g>
          );
        })}

        {/* Animated flow on active edges */}
        {EDGES.map(([fId, tId]) => {
          const f = POSITIONS[fId];
          const t = POSITIONS[tId];
          const fn = byId[fId];
          const tn = byId[tId];
          if (!f || !t || !fn?.active || !tn?.active) return null;
          const isEscalation = tId === 4 || tId === 7 || tId === 8;
          const color = isEscalation ? '#ff6600' : '#00dd66';

          return (
            <motion.circle
              key={`flow${fId}-${tId}`}
              r="0.7"
              fill={color}
              filter="url(#glow)"
              initial={{ cx: f.x, cy: f.y }}
              animate={{ cx: t.x, cy: t.y }}
              transition={{ duration: 1.8, repeat: Infinity, ease: 'linear', delay: fId * 0.3 }}
            />
          );
        })}

        {/* Nodes */}
        {nodes.map(n => {
          const pos = POSITIONS[n.id];
          if (!pos) return null;
          const probPct = (n.probability * 100).toFixed(n.probability < 0.01 ? 2 : 1);

          return (
            <g key={n.id}>
              {/* Node ring (active glow) */}
              {n.active && (
                <motion.circle
                  cx={pos.x} cy={pos.y} r={4.5}
                  fill="none"
                  stroke={n.color}
                  strokeWidth={0.4}
                  opacity={0.4}
                  animate={{ r: [4.5, 6, 4.5], opacity: [0.4, 0.1, 0.4] }}
                  transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
                />
              )}

              {/* Node body */}
              <motion.circle
                cx={pos.x} cy={pos.y} r={3.5}
                fill={n.active ? n.color + '33' : '#050d1a'}
                stroke={n.color}
                strokeWidth={n.active ? 0.7 : 0.4}
                filter={n.active ? 'url(#glow)' : undefined}
                opacity={n.active ? 1 : 0.5}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: n.id * 0.08 }}
              />

              {/* Node ID */}
              <text
                x={pos.x} y={pos.y + 0.9}
                textAnchor="middle"
                fontSize="2.8"
                fill={n.active ? n.color : '#4a7a8f'}
                fontFamily="monospace"
                fontWeight="bold"
              >
                {n.id}
              </text>

              {/* Node name */}
              <text
                x={pos.x}
                y={pos.y + 6.5}
                textAnchor="middle"
                fontSize="2.2"
                fill={n.active ? '#a8d8ea' : '#2a4a5f'}
                fontFamily="monospace"
              >
                {n.name}
              </text>

              {/* Probability */}
              <text
                x={pos.x}
                y={pos.y + 9.2}
                textAnchor="middle"
                fontSize="2.0"
                fill={n.active ? n.color : '#1a3a4f'}
                fontFamily="monospace"
              >
                {probPct}%
              </text>
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="absolute bottom-1 left-2 flex gap-3 text-[8px] font-mono">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-px bg-red/70" style={{ border: '0.5px dashed #ff4400' }} />
          <span className="text-dim">ESCALATION PATH</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-px" style={{ border: '0.5px dashed #00aa44' }} />
          <span className="text-dim">DE-ESCALATION</span>
        </span>
      </div>
    </div>
  );
}
