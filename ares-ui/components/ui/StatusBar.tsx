'use client';

import { motion } from 'framer-motion';
import type { SimulationResult } from '@/lib/types';

interface Props {
  result:     SimulationResult;
  isRunning:  boolean;
  apiOnline:  boolean;
}

export default function StatusBar({ result, isRunning, apiOnline }: Props) {
  const top = [...result.outcomes].sort((a, b) => b.probability - a.probability)[0];
  const nuke = result.nuclearRisk;

  return (
    <div
      className="h-8 flex items-center justify-between px-4 border-t border-border bg-surface shrink-0"
      style={{ fontSize: '10px', fontFamily: 'monospace' }}
    >
      {/* Left */}
      <div className="flex items-center gap-4 text-dim">
        <span>
          <span className="text-cyan">▸</span> MOST PROBABLE:{' '}
          <span className="text-text font-semibold">{top?.shortName}</span>{' '}
          <span className="text-amber tabular-nums">
            {(top?.probability * 100).toFixed(1)}%
          </span>
        </span>

        <span className="text-border">|</span>

        <span>
          CASUALTIES (EST):{' '}
          <span className="text-amber tabular-nums">
            {result.casualtyEstimate.israel.toLocaleString()} IL
          </span>{' '}
          /{' '}
          <span className="text-red tabular-nums">
            {result.casualtyEstimate.iran.toLocaleString()} IR
          </span>
        </span>
      </div>

      {/* Center */}
      <div className="flex items-center gap-3">
        {isRunning && (
          <motion.div
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ repeat: Infinity, duration: 0.5 }}
            className="text-amber tracking-widest"
          >
            ◈ SIMULATION RUNNING
          </motion.div>
        )}
      </div>

      {/* Right */}
      <div className="flex items-center gap-4 text-dim">
        <span>
          NUCLEAR RISK:{' '}
          <motion.span
            animate={nuke > 0.15 ? { opacity: [1, 0.5, 1] } : {}}
            transition={{ repeat: Infinity, duration: 1.2 }}
            style={{ color: nuke > 0.15 ? '#ff0033' : nuke > 0.08 ? '#ff8c00' : '#00cc66' }}
            className="tabular-nums font-bold"
          >
            {(nuke * 100).toFixed(2)}%
          </motion.span>
          {nuke > 0.15 && (
            <span className="ml-1 text-red font-bold animate-pulse">⚠ RED</span>
          )}
        </span>

        <span className="text-border">|</span>

        <span>
          ENGINE:{' '}
          <span className={apiOnline ? 'text-green' : 'text-amber'}>
            {apiOnline ? '● PYTHON/ARES' : '● JS FALLBACK'}
          </span>
        </span>

        <span className="text-border">|</span>

        <span className="text-dim/50 tabular-nums">
          v1.0 · ARES © 2025
        </span>
      </div>
    </div>
  );
}
