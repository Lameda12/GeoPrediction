'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import type { EconomicImpact } from '@/lib/types';

interface Props { data: EconomicImpact[] }

const PERIODS = ['6mo', '12mo', '24mo', '36mo'] as const;
type Period = typeof PERIODS[number];

function gdpColor(v: number): string {
  if (v > 2)   return '#00cc66';
  if (v > 0)   return '#66cc88';
  if (v > -1)  return '#88a890';
  if (v > -2)  return '#ccaa00';
  if (v > -4)  return '#ff8c00';
  if (v > -7)  return '#ff4400';
  return '#ff1111';
}

function gdpLabel(v: number): string {
  return (v >= 0 ? '+' : '') + v.toFixed(2) + '%';
}

export default function EconomicHeatmap({ data }: Props) {
  const [tooltip, setTooltip] = useState<{ country: string; period: Period; value: number } | null>(null);

  return (
    <div className="w-full h-full flex flex-col overflow-auto">
      {/* Column headers */}
      <div className="flex items-center mb-1 px-0.5 sticky top-0 bg-panel z-10">
        <div className="w-28 shrink-0 text-[8px] font-mono text-dim tracking-widest">COUNTRY</div>
        {PERIODS.map(p => (
          <div key={p} className="flex-1 text-center text-[8px] font-mono text-dim tracking-widest">
            {p.toUpperCase()}
          </div>
        ))}
        <div className="w-12 text-center text-[8px] font-mono text-dim tracking-widest">OIL%</div>
      </div>

      {/* Rows */}
      <div className="space-y-1">
        {data.map((row, ri) => {
          const vals: Record<Period, number> = {
            '6mo':  row.m6,
            '12mo': row.m12,
            '24mo': row.m24,
            '36mo': row.m36,
          };

          return (
            <motion.div
              key={row.country}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: ri * 0.04 }}
              className="flex items-center"
            >
              {/* Country */}
              <div className="w-28 shrink-0 flex items-center gap-1 pr-1">
                <span className="text-base leading-none">{row.flag}</span>
                <span className="text-[9px] font-mono text-text/80 truncate">{row.country}</span>
              </div>

              {/* GDP cells */}
              {PERIODS.map(period => {
                const v = vals[period];
                const col = gdpColor(v);
                const isHovered = tooltip?.country === row.country && tooltip?.period === period;

                return (
                  <div
                    key={period}
                    className="flex-1 mx-0.5 h-7 flex items-center justify-center cursor-default relative"
                    style={{
                      background: col + '28',
                      border:     `1px solid ${col}${isHovered ? 'cc' : '35'}`,
                      boxShadow:  isHovered ? `0 0 8px ${col}50` : 'none',
                    }}
                    onMouseEnter={() => setTooltip({ country: row.country, period, value: v })}
                    onMouseLeave={() => setTooltip(null)}
                  >
                    <span
                      className="text-[9px] font-mono tabular-nums font-semibold"
                      style={{ color: col, textShadow: `0 0 6px ${col}40` }}
                    >
                      {gdpLabel(v)}
                    </span>
                  </div>
                );
              })}

              {/* Oil dependency bar */}
              <div className="w-12 flex items-center pl-1.5">
                <div className="relative w-full h-2 bg-border">
                  <div
                    className="absolute top-0 left-0 h-full"
                    style={{
                      width: `${Math.abs(row.oilDependency)}%`,
                      background: row.oilDependency < 0 ? '#00cc66' : '#ff8c00',
                    }}
                  />
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div className="mt-2 border border-border bg-surface px-3 py-1.5 text-[9px] font-mono">
          <span className="text-dim">{tooltip.country} · {tooltip.period.toUpperCase()} GDP IMPACT: </span>
          <span style={{ color: gdpColor(tooltip.value) }} className="font-bold">
            {gdpLabel(tooltip.value)}
          </span>
        </div>
      )}

      {/* Scale legend */}
      <div className="mt-3 flex items-center gap-1 flex-wrap">
        {[
          ['>+2%',   '#00cc66'],
          ['0–+2%',  '#66cc88'],
          ['0–-2%',  '#ccaa00'],
          ['-2–-4%', '#ff8c00'],
          ['-4–-7%', '#ff4400'],
          ['<-7%',   '#ff1111'],
        ].map(([label, color]) => (
          <div key={label} className="flex items-center gap-0.5">
            <div className="w-8 h-2" style={{ background: color + '55', border: `1px solid ${color}40` }} />
            <span className="text-[8px] font-mono" style={{ color }}>{label}</span>
          </div>
        ))}
        <span className="text-[8px] font-mono text-dim/50 ml-1">GDP Δ%</span>
      </div>
    </div>
  );
}
