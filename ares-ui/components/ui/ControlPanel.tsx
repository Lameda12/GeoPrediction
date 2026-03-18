'use client';

import { motion } from 'framer-motion';
import type { SimulationParams } from '@/lib/types';

interface Props {
  params:      SimulationParams;
  onChange:    (p: Partial<SimulationParams>) => void;
  onRun:       () => void;
  isRunning:   boolean;
  durationMs?: number;
}

interface SliderDef {
  key:    keyof SimulationParams;
  label:  string;
  min:    number;
  max:    number;
  step:   number;
  format: (v: number) => string;
  color:  string;
}

const SLIDERS: SliderDef[] = [
  { key: 'strikeIntensity',     label: 'STRIKE INTENSITY',       min: 1,   max: 10,  step: 0.1,  format: v => v.toFixed(1) + '/10',  color: '#ff8c00' },
  { key: 'allianceReliability', label: 'ALLIANCE RELIABILITY',   min: 0,   max: 1,   step: 0.01, format: v => (v*100).toFixed(0)+'%', color: '#00ccff' },
  { key: 'oilDisruptionPct',    label: 'HORMUZ DISRUPTION',      min: 0,   max: 100, step: 1,    format: v => v.toFixed(0) + '%',     color: '#ffcc00' },
  { key: 'iranRetaliationProb', label: 'IRAN RETALIATION PROB',  min: 0,   max: 1,   step: 0.01, format: v => (v*100).toFixed(0)+'%', color: '#ff2020' },
  { key: 'nuclearDeterrence',   label: 'NUCLEAR DETERRENCE',     min: 0,   max: 1,   step: 0.01, format: v => (v*100).toFixed(0)+'%', color: '#cc44ff' },
];

const INVOLVEMENT_OPTS = [
  { value: 'isr_support',   label: 'ISR SUPPORT ONLY'   },
  { value: 'direct_strike', label: 'DIRECT AIR STRIKE'  },
  { value: 'full_war',      label: 'FULL ENGAGEMENT'    },
] as const;

const RUN_OPTIONS = [1000, 5000, 10000, 50000];

export default function ControlPanel({ params, onChange, onRun, isRunning, durationMs }: Props) {
  return (
    <div className="flex flex-col h-full overflow-y-auto bg-panel border-r border-border">
      {/* Header */}
      <div className="px-3 py-2 border-b border-border bg-surface">
        <span className="text-[10px] font-mono tracking-[0.22em] text-dim uppercase">
          ◈ Scenario Parameters
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-5">

        {/* Scenario label */}
        <div className="border border-amber/30 bg-amber/5 px-3 py-2">
          <div className="text-[9px] font-mono text-dim tracking-widest mb-0.5">ACTIVE SCENARIO</div>
          <div className="text-amber font-mono text-[11px] font-semibold tracking-wide">
            USA + ISRAEL vs IRAN
          </div>
          <div className="text-dim/60 text-[9px] font-mono mt-0.5">
            Correlates of War · IISS 2024 · SIPRI
          </div>
        </div>

        {/* US Involvement */}
        <div>
          <div className="text-[9px] font-mono text-dim tracking-widest mb-2 uppercase">
            US Involvement Level
          </div>
          <div className="space-y-1">
            {INVOLVEMENT_OPTS.map(opt => (
              <button
                key={opt.value}
                onClick={() => onChange({ usInvolvement: opt.value })}
                className="w-full text-left px-2 py-1.5 border text-[10px] font-mono tracking-wider transition-all"
                style={params.usInvolvement === opt.value ? {
                  borderColor: '#00ccff80',
                  background:  '#00ccff14',
                  color:       '#00ccff',
                } : {
                  borderColor: '#0e2d4a',
                  color:       '#4a7a8f',
                }}
              >
                {params.usInvolvement === opt.value ? '▶ ' : '  '}{opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Sliders */}
        {SLIDERS.map(s => {
          const val = params[s.key] as number;
          const pct = ((val - s.min) / (s.max - s.min)) * 100;
          return (
            <div key={s.key}>
              <div className="flex justify-between items-center mb-1.5">
                <span className="text-[9px] font-mono text-dim tracking-widest uppercase">
                  {s.label}
                </span>
                <span className="text-[11px] font-mono tabular-nums" style={{ color: s.color }}>
                  {s.format(val)}
                </span>
              </div>
              <div className="relative h-1.5 bg-border rounded-sm">
                <div
                  className="absolute top-0 left-0 h-full rounded-sm transition-all"
                  style={{ width: `${pct}%`, background: s.color, boxShadow: `0 0 6px ${s.color}60` }}
                />
              </div>
              <input
                type="range"
                min={s.min} max={s.max} step={s.step}
                value={val}
                onChange={e => onChange({ [s.key]: parseFloat(e.target.value) })}
                className="w-full mt-1 opacity-0 absolute"
                style={{ height: '20px', marginTop: '-10px', cursor: 'pointer' }}
              />
              {/* Accessible range - overlay */}
              <input
                type="range"
                min={s.min} max={s.max} step={s.step}
                value={val}
                onChange={e => onChange({ [s.key]: parseFloat(e.target.value) })}
                className="w-full mt-1 cursor-pointer"
                style={{
                  appearance: 'none',
                  background: 'transparent',
                  height: '14px',
                  outline: 'none',
                  padding: '4px 0',
                }}
              />
            </div>
          );
        })}

        {/* Simulation Runs */}
        <div>
          <div className="text-[9px] font-mono text-dim tracking-widest mb-2 uppercase">
            Monte Carlo Runs (N)
          </div>
          <div className="grid grid-cols-2 gap-1">
            {RUN_OPTIONS.map(n => (
              <button
                key={n}
                onClick={() => onChange({ simulationRuns: n })}
                className="px-2 py-1.5 border text-[10px] font-mono tracking-wider transition-all"
                style={params.simulationRuns === n ? {
                  borderColor: '#ff8c0080',
                  background:  '#ff8c0014',
                  color:       '#ff8c00',
                } : {
                  borderColor: '#0e2d4a',
                  color:       '#4a7a8f',
                }}
              >
                {n.toLocaleString()}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Run button */}
      <div className="p-3 border-t border-border">
        {durationMs && !isRunning && (
          <div className="text-[9px] font-mono text-dim text-center mb-2">
            Last run: {durationMs}ms · CI 95%
          </div>
        )}
        <motion.button
          onClick={onRun}
          disabled={isRunning}
          whileHover={{ scale: isRunning ? 1 : 1.01 }}
          whileTap={{ scale: isRunning ? 1 : 0.98 }}
          className="w-full py-2.5 font-mono text-sm font-bold tracking-[0.25em] uppercase border transition-all disabled:opacity-50"
          style={isRunning ? {
            borderColor: '#ff8c0060',
            color:       '#ff8c0080',
            background:  '#ff8c0008',
          } : {
            borderColor: '#ff8c00',
            color:       '#ff8c00',
            background:  '#ff8c0015',
            boxShadow:   '0 0 12px rgba(255,140,0,0.3)',
          }}
        >
          {isRunning ? (
            <motion.span
              animate={{ opacity: [1, 0.4, 1] }}
              transition={{ repeat: Infinity, duration: 0.7 }}
            >
              ◈ COMPUTING...
            </motion.span>
          ) : (
            '▶ RUN SIMULATION'
          )}
        </motion.button>
        <div className="mt-2 text-[8px] font-mono text-dim/40 text-center">
          [MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE]
        </div>
      </div>
    </div>
  );
}
