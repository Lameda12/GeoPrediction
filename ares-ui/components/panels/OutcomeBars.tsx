'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';
import type { OutcomeState } from '@/lib/types';

const SEVERITY_COLOR: Record<string, string> = {
  safe:     '#00cc66',
  low:      '#44aacc',
  moderate: '#ffcc00',
  high:     '#ff8c00',
  critical: '#ff2020',
};

function AnimatedNumber({ value, decimals = 1 }: { value: number; decimals?: number }) {
  const [display, setDisplay] = useState(0);
  const target = useRef(value);
  useEffect(() => {
    target.current = value;
    let start: number | null = null;
    const from = display;
    const to   = value;
    const dur  = 700;
    const step = (ts: number) => {
      if (!start) start = ts;
      const prog = Math.min((ts - start) / dur, 1);
      const ease = 1 - Math.pow(1 - prog, 3);
      setDisplay(from + (to - from) * ease);
      if (prog < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);
  return <>{display.toFixed(decimals)}</>;
}

export default function OutcomeBars({ outcomes }: { outcomes: OutcomeState[] }) {
  const maxP = Math.max(...outcomes.map(o => o.probability));

  return (
    <div className="space-y-2.5">
      {outcomes.map((o, i) => {
        const color = SEVERITY_COLOR[o.severity];
        const pct   = (o.probability / maxP) * 100;
        const lo    = (o.ciLow / maxP) * 100;
        const hi    = (o.ciHigh / maxP) * 100;

        return (
          <motion.div
            key={o.id}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.06, duration: 0.3 }}
          >
            {/* Label row */}
            <div className="flex justify-between items-baseline mb-1">
              <div className="flex items-center gap-1.5">
                <span
                  className="text-[9px] font-mono tabular-nums w-4 text-right"
                  style={{ color: color + 'aa' }}
                >
                  {o.id}
                </span>
                <span className="text-[10px] font-mono text-text/80 truncate max-w-[170px]">
                  {o.name}
                </span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-[9px] font-mono text-dim">
                  [{(o.ciLow * 100).toFixed(1)}–{(o.ciHigh * 100).toFixed(1)}]
                </span>
                <span
                  className="text-[12px] font-mono font-bold tabular-nums w-12 text-right"
                  style={{ color, textShadow: `0 0 8px ${color}60` }}
                >
                  <AnimatedNumber value={o.probability * 100} />%
                </span>
              </div>
            </div>

            {/* Bar track */}
            <div className="relative h-3 bg-border/50 overflow-hidden">
              {/* CI band */}
              <div
                className="absolute top-0 h-full opacity-25"
                style={{ left: `${lo}%`, width: `${hi - lo}%`, background: color }}
              />
              {/* Main bar */}
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ delay: i * 0.06 + 0.15, duration: 0.6, ease: 'easeOut' }}
                className="absolute top-0 left-0 h-full"
                style={{
                  background:  `linear-gradient(90deg, ${color}80, ${color})`,
                  boxShadow:   `0 0 6px ${color}60`,
                }}
              />
            </div>
          </motion.div>
        );
      })}

      <div className="mt-3 pt-2 border-t border-border text-[8px] font-mono text-dim/50">
        95% CONFIDENCE INTERVALS SHOWN · N = MONTE CARLO RUNS · [MODEL — NOT INTELLIGENCE]
      </div>
    </div>
  );
}
