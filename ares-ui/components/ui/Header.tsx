'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface Props {
  apiOnline:     boolean;
  nuclearRisk:   number;
  runsCompleted: number;
  isRunning:     boolean;
}

const THREAT_LEVELS = [
  { label: 'GUARDED',  color: '#00cc66', min: 0.00 },
  { label: 'ELEVATED', color: '#ffcc00', min: 0.05 },
  { label: 'HIGH',     color: '#ff8c00', min: 0.10 },
  { label: 'SEVERE',   color: '#ff4000', min: 0.15 },
  { label: 'CRITICAL', color: '#ff0000', min: 0.22 },
];

function getThreatLevel(risk: number) {
  let level = THREAT_LEVELS[0];
  for (const l of THREAT_LEVELS) if (risk >= l.min) level = l;
  return level;
}

export default function Header({ apiOnline, nuclearRisk, runsCompleted, isRunning }: Props) {
  const [clock, setClock] = useState('');
  const threat            = getThreatLevel(nuclearRisk);

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setClock(
        now.toISOString().replace('T', ' ').slice(0, 19) + ' UTC',
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header
      className="h-12 flex items-center justify-between px-4 border-b border-border bg-surface shrink-0"
      style={{ boxShadow: '0 1px 0 rgba(26,95,138,0.4)' }}
    >
      {/* Left — branding */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div
            className="w-6 h-6 flex items-center justify-center border border-amber/60 text-amber text-[11px] font-bold"
            style={{ textShadow: '0 0 8px #ff8c00' }}
          >
            ⬡
          </div>
          <span className="text-text font-mono text-sm font-semibold tracking-[0.18em]">
            ARES
          </span>
          <span className="text-dim font-mono text-[10px] tracking-widest">
            ADAPTIVE RISK & ESCALATION SIMULATOR
          </span>
        </div>

        <div className="h-4 w-px bg-border" />

        <span className="text-[9px] font-mono text-amber/80 tracking-wider border border-amber/30 px-2 py-0.5">
          [MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE]
        </span>
      </div>

      {/* Center — threat level */}
      <div className="flex items-center gap-3">
        <span className="text-[10px] font-mono text-dim tracking-widest">THREAT INDEX</span>
        <motion.div
          animate={{ opacity: [1, 0.6, 1] }}
          transition={{ repeat: Infinity, duration: 1.8 }}
          className="flex items-center gap-1.5 px-3 py-1 border text-[11px] font-mono font-bold tracking-widest"
          style={{
            color:       threat.color,
            borderColor: threat.color + '70',
            background:  threat.color + '14',
            textShadow:  `0 0 8px ${threat.color}`,
          }}
        >
          ● {threat.label}
        </motion.div>
      </div>

      {/* Right — status */}
      <div className="flex items-center gap-4 text-[10px] font-mono">
        {/* Simulation count */}
        <div className="text-dim">
          <span className="text-cyan">{runsCompleted.toLocaleString()}</span> RUNS
        </div>

        {/* Engine status */}
        <div className="flex items-center gap-1.5">
          {isRunning ? (
            <motion.span
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ repeat: Infinity, duration: 0.6 }}
              className="text-amber"
            >
              ◈
            </motion.span>
          ) : (
            <span className={apiOnline ? 'text-green' : 'text-amber'}>●</span>
          )}
          <span className="text-dim">
            {isRunning ? 'COMPUTING' : apiOnline ? 'ENGINE: PYTHON' : 'ENGINE: JS'}
          </span>
        </div>

        {/* Clock — suppressHydrationWarning prevents mismatch between SSR empty string and live time */}
        <div className="text-dim/70 tabular-nums" suppressHydrationWarning>{clock}</div>
      </div>
    </header>
  );
}
