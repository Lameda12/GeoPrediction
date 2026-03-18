'use client';

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Legend,
} from 'recharts';
import { motion } from 'framer-motion';
import type { ActorAttrition } from '@/lib/types';

interface Props {
  attrition: ActorAttrition[];
  showOil?:  boolean;
  oilData?:  Array<{ month: number; price: number; pessimistic: number; optimistic: number }>;
}

const TICK_STYLE = { fill: '#4a7a8f', fontSize: 9, fontFamily: 'JetBrains Mono, monospace' };

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="border border-border bg-panel px-3 py-2 text-[10px] font-mono"
      style={{ boxShadow: '0 0 12px rgba(0,0,0,0.8)' }}
    >
      <div className="text-dim mb-1">DAY {label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex justify-between gap-4" style={{ color: p.color }}>
          <span className="truncate max-w-[110px]">{p.name}</span>
          <span className="tabular-nums font-bold">{p.value.toFixed(1)}%</span>
        </div>
      ))}
    </div>
  );
}

function OilTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="border border-border bg-panel px-3 py-2 text-[10px] font-mono">
      <div className="text-dim mb-1">MONTH {label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} style={{ color: p.color }} className="flex justify-between gap-4">
          <span>{p.name}</span>
          <span className="tabular-nums font-bold">${p.value.toFixed(2)}/bbl</span>
        </div>
      ))}
    </div>
  );
}

// Merge all actor series into a single data array for Recharts
function buildChartData(attrition: ActorAttrition[]) {
  if (!attrition.length) return [];
  const allDays = attrition[0].data.map(d => d.day);
  return allDays.map(day => {
    const row: Record<string, number> = { day };
    attrition.forEach(a => {
      const pt = a.data.find(d => d.day === day);
      if (pt) row[a.key] = pt.strength;
    });
    return row;
  });
}

export default function AttritionChart({ attrition, showOil, oilData }: Props) {
  if (showOil && oilData) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="w-full h-full flex flex-col">
        <div className="text-[9px] font-mono text-dim tracking-widest mb-2 px-1">
          BRENT CRUDE FORECAST ($/bbl) · 36-MONTH WINDOW
        </div>
        <ResponsiveContainer width="100%" height="85%">
          <LineChart data={oilData} margin={{ top: 2, right: 8, left: -8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="2 4" stroke="#0e2d4a" vertical={false} />
            <XAxis dataKey="month" tick={TICK_STYLE} tickFormatter={m => `M${m}`} interval={3} />
            <YAxis tick={TICK_STYLE} tickFormatter={v => `$${v}`} domain={['auto', 'auto']} />
            <Tooltip content={<OilTooltip />} />
            <Line type="monotone" dataKey="pessimistic" stroke="#ff2020" dot={false} strokeWidth={1} strokeDasharray="3 2" name="Pessimistic" />
            <Line type="monotone" dataKey="price"       stroke="#ffcc00" dot={false} strokeWidth={2} name="Baseline" />
            <Line type="monotone" dataKey="optimistic"  stroke="#00cc66" dot={false} strokeWidth={1} strokeDasharray="3 2" name="Optimistic" />
            <ReferenceLine y={85}  stroke="#4a7a8f" strokeDasharray="2 4" label={{ value: 'Pre-conflict', fill: '#4a7a8f', fontSize: 8 }} />
          </LineChart>
        </ResponsiveContainer>
      </motion.div>
    );
  }

  const chartData = buildChartData(attrition);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="w-full h-full flex flex-col">
      <div className="text-[9px] font-mono text-dim tracking-widest mb-2 px-1">
        COMBAT EFFECTIVE STRENGTH (%) · LANCHESTER MODEL · 90-DAY
      </div>
      <ResponsiveContainer width="100%" height="88%">
        <LineChart data={chartData} margin={{ top: 2, right: 8, left: -14, bottom: 0 }}>
          <CartesianGrid strokeDasharray="2 4" stroke="#0e2d4a" vertical={false} />
          <XAxis dataKey="day" tick={TICK_STYLE} tickFormatter={d => `D${d}`} interval={14} />
          <YAxis tick={TICK_STYLE} domain={[0, 100]} tickFormatter={v => `${v}%`} />
          <Tooltip content={<CustomTooltip />} />

          {/* Phase reference lines */}
          <ReferenceLine x={7}  stroke="#ff8c0040" strokeDasharray="2 3" label={{ value: 'D7',  fill: '#ff8c0060', fontSize: 8 }} />
          <ReferenceLine x={30} stroke="#ff8c0040" strokeDasharray="2 3" label={{ value: 'D30', fill: '#ff8c0060', fontSize: 8 }} />

          {attrition.map(a => (
            <Line
              key={a.key}
              type="monotone"
              dataKey={a.key}
              stroke={a.color}
              name={a.actor}
              dot={false}
              strokeWidth={a.key === 'usa' ? 1.5 : 2}
              strokeDasharray={a.key === 'usa' ? '4 2' : undefined}
              style={{ filter: `drop-shadow(0 0 3px ${a.color}60)` }}
            />
          ))}

          <Legend
            iconSize={8}
            wrapperStyle={{ fontSize: '9px', fontFamily: 'JetBrains Mono, monospace', paddingTop: '4px' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
