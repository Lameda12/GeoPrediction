'use client';

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { motion, AnimatePresence } from 'framer-motion';

import Header       from '@/components/ui/Header';
import StatusBar    from '@/components/ui/StatusBar';
import ControlPanel from '@/components/ui/ControlPanel';
import PanelWrapper from '@/components/ui/PanelWrapper';
import OutcomeBars     from '@/components/panels/OutcomeBars';
import EscalationGraph from '@/components/panels/EscalationGraph';
import AttritionChart  from '@/components/panels/AttritionChart';
import EconomicHeatmap from '@/components/panels/EconomicHeatmap';

import { DEFAULT_PARAMS, runSimulation, checkApiHealth } from '@/lib/simulation';
import { generateMockData }                              from '@/lib/mockData';
import type { SimulationParams, SimulationResult }       from '@/lib/types';

// Globe loaded client-side only — avoids SSR crash on Three.js
const Globe3D = dynamic(() => import('@/components/Globe3D'), { ssr: false });

type Tab = 'outcomes' | 'escalation' | 'attrition' | 'oil' | 'economic';

const TABS: { id: Tab; label: string }[] = [
  { id: 'outcomes',   label: 'OUTCOMES'   },
  { id: 'escalation', label: 'ESCALATION' },
  { id: 'attrition',  label: 'ATTRITION'  },
  { id: 'oil',        label: 'OIL CURVE'  },
  { id: 'economic',   label: 'ECONOMIC'   },
];

export default function AresDashboard() {
  const [params,      setParams]    = useState<SimulationParams>(DEFAULT_PARAMS);
  const [result,      setResult]    = useState<SimulationResult | null>(null);
  const [isRunning,   setIsRunning] = useState(false);
  const [activeTab,   setActiveTab] = useState<Tab>('outcomes');
  const [apiOnline,   setApiOnline] = useState(false);
  const [showArcs,    setShowArcs]  = useState(true);
  const [sidebarOpen, setSidebar]   = useState(true);

  // Generate initial data client-side only (avoids SSR/client hydration mismatch)
  useEffect(() => {
    setResult(generateMockData(DEFAULT_PARAMS));
    checkApiHealth().then(setApiOnline);
  }, []);

  const handleRun = useCallback(async () => {
    setIsRunning(true);
    try {
      const r = await runSimulation(params);
      setResult(r);
    } finally {
      setIsRunning(false);
    }
  }, [params]);

  const handleParamChange = useCallback((patch: Partial<SimulationParams>) => {
    setParams(p => ({ ...p, ...patch }));
  }, []);

  // Re-run on parameter change (debounced for sliders)
  useEffect(() => {
    const id = setTimeout(() => {
      setResult(generateMockData(params));
    }, 250);
    return () => clearTimeout(id);
  }, [params]);

  // Show boot screen until client hydrates
  if (!result) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-base gap-4">
        <div className="text-amber font-mono text-lg tracking-[0.3em] animate-pulse">◈ ARES</div>
        <div className="text-dim font-mono text-xs tracking-widest">INITIALIZING SIMULATION ENGINE...</div>
        <div className="w-48 h-px bg-border relative overflow-hidden">
          <div className="absolute inset-y-0 left-0 w-1/3 bg-amber/60 animate-[slide_1s_linear_infinite]" />
        </div>
        <style>{`@keyframes slide { from{transform:translateX(-100%)} to{transform:translateX(400%)} }`}</style>
      </div>
    );
  }

  const badgeForTab = (tab: Tab): string | undefined => {
    if (tab === 'outcomes') {
      const top = [...result.outcomes].sort((a, b) => b.probability - a.probability)[0];
      return top ? `${(top.probability * 100).toFixed(1)}%` : undefined;
    }
    if (tab === 'escalation') return result.nuclearRisk > 0.15 ? '⚠ RED' : undefined;
    return undefined;
  };

  const badgeColor = (tab: Tab) =>
    tab === 'escalation' && result.nuclearRisk > 0.15 ? '#ff2020' : '#ff8c00';

  return (
    <div className="flex flex-col h-screen bg-base overflow-hidden">
      {/* ── Top header ── */}
      <Header
        apiOnline={apiOnline}
        nuclearRisk={result.nuclearRisk}
        runsCompleted={result.runsCompleted}
        isRunning={isRunning}
      />

      {/* ── Main content ── */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* ── Left sidebar (controls) ── */}
        <AnimatePresence initial={false}>
          {sidebarOpen && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 228, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.22, ease: 'easeInOut' }}
              className="h-full overflow-hidden shrink-0"
            >
              <ControlPanel
                params={params}
                onChange={handleParamChange}
                onRun={handleRun}
                isRunning={isRunning}
                durationMs={result.durationMs}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Globe + panels ── */}
        <div className="flex-1 min-w-0 flex flex-col overflow-hidden">

          {/* Globe strip — toggle sidebar, arc controls */}
          <div className="flex items-center gap-2 px-2 py-1 border-b border-border bg-surface shrink-0">
            <button
              onClick={() => setSidebar(v => !v)}
              className="text-[9px] font-mono text-dim hover:text-cyan border border-border hover:border-cyan/50 px-2 py-0.5 transition-colors"
            >
              {sidebarOpen ? '◀ PARAMS' : '▶ PARAMS'}
            </button>
            <button
              onClick={() => setShowArcs(v => !v)}
              className="text-[9px] font-mono transition-colors border px-2 py-0.5"
              style={showArcs
                ? { color: '#ff8c00', borderColor: '#ff8c0060', background: '#ff8c0012' }
                : { color: '#4a7a8f', borderColor: '#0e2d4a' }}
            >
              {showArcs ? '◈ STRIKE ARCS ON' : '○ STRIKE ARCS OFF'}
            </button>
            <div className="flex-1" />
            {/* Scenario phase indicator */}
            <div className="flex items-center gap-3 text-[9px] font-mono text-dim">
              {[
                { label: 'D1-7  INITIAL EXCHANGE',   color: '#ff8c00' },
                { label: 'D7-30 ESCALATION WINDOW',  color: '#ffcc00' },
                { label: 'D30-90 ECONOMIC CONTAGION', color: '#ff5500' },
              ].map(({ label, color }) => (
                <span key={label} className="flex items-center gap-1">
                  <span style={{ color }}>■</span>
                  <span>{label}</span>
                </span>
              ))}
            </div>
          </div>

          <div className="flex flex-1 min-h-0 overflow-hidden">
            {/* Globe */}
            <div className="flex-1 relative min-w-0 border-r border-border">
              <Globe3D
                result={result}
                activeArcs={showArcs}
                usInvolvement={params.usInvolvement}
              />

              {/* Globe overlay: nuclear risk meter */}
              <div
                className="absolute bottom-4 left-4 border border-border bg-panel/80 px-3 py-2 text-[10px] font-mono backdrop-blur-sm"
                style={{ minWidth: 170 }}
              >
                <div className="text-dim tracking-widest mb-1.5 text-[8px]">NUCLEAR RISK INDEX</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-border relative overflow-hidden">
                    <motion.div
                      className="absolute inset-y-0 left-0"
                      animate={{ width: `${result.nuclearRisk * 100}%` }}
                      transition={{ duration: 0.5 }}
                      style={{
                        background: result.nuclearRisk > 0.15
                          ? 'linear-gradient(90deg, #ff4400, #ff0000)'
                          : result.nuclearRisk > 0.08
                          ? 'linear-gradient(90deg, #cc6600, #ff8c00)'
                          : 'linear-gradient(90deg, #007744, #00cc66)',
                        boxShadow: `0 0 8px ${result.nuclearRisk > 0.15 ? '#ff000060' : '#ff8c0040'}`,
                      }}
                    />
                  </div>
                  <span
                    className="tabular-nums font-bold"
                    style={{ color: result.nuclearRisk > 0.15 ? '#ff2020' : result.nuclearRisk > 0.08 ? '#ff8c00' : '#00cc66' }}
                  >
                    {(result.nuclearRisk * 100).toFixed(2)}%
                  </span>
                </div>
                {result.nuclearRisk > 0.15 && (
                  <motion.div
                    animate={{ opacity: [1, 0.4, 1] }}
                    transition={{ repeat: Infinity, duration: 0.8 }}
                    className="mt-1 text-[9px] text-red font-bold"
                  >
                    ⚠ THRESHOLD EXCEEDED — MONITOR
                  </motion.div>
                )}
              </div>

              {/* Casualty estimate overlay */}
              <div className="absolute bottom-4 right-4 border border-border bg-panel/80 px-3 py-2 text-[10px] font-mono backdrop-blur-sm">
                <div className="text-dim tracking-widest mb-1 text-[8px]">CASUALTY ESTIMATE (MODEL)</div>
                <div className="space-y-0.5">
                  <div className="flex justify-between gap-4">
                    <span className="text-amber">🇮🇱 Israel</span>
                    <span className="tabular-nums">{result.casualtyEstimate.israel.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-red">🇮🇷 Iran</span>
                    <span className="tabular-nums">{result.casualtyEstimate.iran.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between gap-4 border-t border-border pt-0.5 mt-0.5">
                    <span className="text-dim">Civilian</span>
                    <span className="tabular-nums text-dim">{result.casualtyEstimate.civilian.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right panels */}
            <div className="w-[400px] shrink-0 flex flex-col min-h-0">
              {/* Tab bar */}
              <div className="flex border-b border-border bg-surface shrink-0">
                {TABS.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className="flex-1 py-2 text-[9px] font-mono tracking-wider border-r border-border last:border-r-0 transition-all relative"
                    style={activeTab === tab.id ? {
                      color: '#ff8c00',
                      background: 'rgba(255,140,0,0.08)',
                      borderBottom: '2px solid #ff8c00',
                    } : {
                      color: '#4a7a8f',
                    }}
                  >
                    {tab.label}
                    {badgeForTab(tab.id) && (
                      <span
                        className="absolute top-0.5 right-0.5 text-[7px] font-bold px-0.5"
                        style={{ color: badgeColor(tab.id) }}
                      >
                        {badgeForTab(tab.id)}
                      </span>
                    )}
                  </button>
                ))}
              </div>

              {/* Panel content */}
              <div className="flex-1 min-h-0 overflow-hidden">
                <AnimatePresence mode="wait">
                  {activeTab === 'outcomes' && (
                    <motion.div key="outcomes" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full overflow-y-auto p-3">
                      <PanelWrapper
                        title="Monte Carlo Outcome Distribution"
                        subtitle={`N=${result.runsCompleted.toLocaleString()} · 95% CI`}
                        badge="8 STATES"
                        className="min-h-full"
                      >
                        <OutcomeBars outcomes={result.outcomes} />
                      </PanelWrapper>
                    </motion.div>
                  )}

                  {activeTab === 'escalation' && (
                    <motion.div key="escalation" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full p-3">
                      <PanelWrapper
                        title="Escalation Ladder"
                        subtitle="Bayesian Decision Tree"
                        badge={result.nuclearRisk > 0.15 ? '⚠ RED FLAG' : 'NOMINAL'}
                        badgeColor={result.nuclearRisk > 0.15 ? '#ff2020' : '#00cc66'}
                        className="h-full"
                        noPad
                      >
                        <div className="h-full p-2">
                          <EscalationGraph nodes={result.escalationNodes} />
                        </div>
                      </PanelWrapper>
                    </motion.div>
                  )}

                  {activeTab === 'attrition' && (
                    <motion.div key="attrition" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full p-3">
                      <PanelWrapper
                        title="Force Attrition — Lanchester Model"
                        subtitle="Combat Effective Strength %"
                        badge="SQUARE LAW"
                        className="h-full"
                        noPad
                      >
                        <div className="h-full p-3">
                          <AttritionChart attrition={result.attrition} />
                        </div>
                      </PanelWrapper>
                    </motion.div>
                  )}

                  {activeTab === 'oil' && (
                    <motion.div key="oil" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full p-3">
                      <PanelWrapper
                        title="Oil Price Trajectory"
                        subtitle="Hormuz Disruption → Brent Crude"
                        badge="LEONTIEF"
                        className="h-full"
                        noPad
                      >
                        <div className="h-full p-3">
                          <AttritionChart
                            attrition={[]}
                            showOil
                            oilData={result.oilPriceTrajectory}
                          />
                        </div>
                      </PanelWrapper>
                    </motion.div>
                  )}

                  {activeTab === 'economic' && (
                    <motion.div key="economic" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full p-3">
                      <PanelWrapper
                        title="Economic Shock Propagation"
                        subtitle="GDP Impact % · Leontief I-O Model"
                        badge="GLOBAL"
                        className="h-full"
                        noPad
                      >
                        <div className="h-full p-3">
                          <EconomicHeatmap data={result.economic} />
                        </div>
                      </PanelWrapper>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Status bar ── */}
      <StatusBar result={result} isRunning={isRunning} apiOnline={apiOnline} />
    </div>
  );
}
