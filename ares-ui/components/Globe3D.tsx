'use client';

import { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import type { SimulationResult, MissileArc, ConflictLocation } from '@/lib/types';
import {
  CONFLICT_LOCATIONS,
  MISSILE_ARCS,
  COUNTRIES_OF_INTEREST,
  COUNTRY_COLORS,
  SEVERITY_RING_COLOR,
} from '@/lib/geodata';

interface Props {
  result:             SimulationResult;
  activeArcs:         boolean;
  usInvolvement:      string;
  onLocationClick?:   (name: string) => void;
}

// Point of view: centred on Middle East
const DEFAULT_POV = { lat: 28, lng: 43, altitude: 2.2 };

export default function Globe3D({ result, activeArcs, usInvolvement, onLocationClick }: Props) {
  const globeRef    = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [GlobeGL, setGlobeGL]   = useState<any>(null);
  const [countries, setCountries] = useState<any>({ features: [] });
  const [dims, setDims]          = useState({ w: 0, h: 0 });
  const [hovered, setHovered]    = useState<string | null>(null);

  // Load globe component client-side only
  useEffect(() => {
    import('react-globe.gl').then(m => setGlobeGL(() => m.default));
  }, []);

  // Load world GeoJSON
  useEffect(() => {
    fetch('https://raw.githubusercontent.com/vasturiano/react-globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson')
      .then(r => r.json())
      .then(setCountries)
      .catch(() => console.warn('[ARES Globe] Could not load GeoJSON'));
  }, []);

  // Container size observer
  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(([e]) => {
      setDims({ w: e.contentRect.width, h: e.contentRect.height });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  // Camera setup + auto-rotate
  useEffect(() => {
    if (!globeRef.current || !GlobeGL) return;
    globeRef.current.pointOfView(DEFAULT_POV, 1000);
    globeRef.current.controls().autoRotate = true;
    globeRef.current.controls().autoRotateSpeed = 0.18;
    globeRef.current.controls().enableDamping = true;
  }, [GlobeGL]);

  const filteredPolygons = useMemo(() =>
    countries.features?.filter((f: any) =>
      COUNTRIES_OF_INTEREST.includes(f.properties?.ADMIN),
    ) ?? [],
    [countries],
  );

  const arcsData: MissileArc[] = useMemo(() => {
    const isUSA = usInvolvement !== 'isr_support';
    return MISSILE_ARCS.filter(a => {
      if (a.actor === 'usa') return isUSA && activeArcs;
      return activeArcs;
    });
  }, [activeArcs, usInvolvement]);

  const ringsData = useMemo(() =>
    CONFLICT_LOCATIONS.filter(l => l.active),
    [],
  );

  const ringColorFn = useCallback(
    (d: any) => {
      const rgb = SEVERITY_RING_COLOR[d.severity] ?? '0,200,255';
      return (t: number) => `rgba(${rgb},${1 - t})`;
    },
    [],
  );

  const pointColorFn = useCallback((d: any) => {
    const MAP: Record<string, string> = {
      nuclear_target: '#ff2020',
      military:       '#ff8c00',
      naval:          '#00aaff',
      proxy:          '#ff5500',
      command:        '#ffcc00',
    };
    return MAP[d.type] ?? '#ffffff';
  }, []);

  const polygonCapFn = useCallback((f: any) => {
    const name = f.properties?.ADMIN;
    return COUNTRY_COLORS[name] ?? 'rgba(255,255,255,0.04)';
  }, []);

  const labelColorFn = useCallback((d: any) => {
    if (d.severity === 'critical') return '#ff4040';
    if (d.severity === 'high')     return '#ffaa00';
    return '#88ccff';
  }, []);

  if (!GlobeGL) {
    return (
      <div ref={containerRef} className="w-full h-full flex items-center justify-center bg-base">
        <div className="text-cyan font-mono text-sm tracking-widest animate-pulse">
          ◈ INITIALIZING GLOBE ENGINE...
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="w-full h-full relative overflow-hidden">
      {/* Vignette overlay */}
      <div
        className="absolute inset-0 pointer-events-none z-10"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,2,5,0.75) 100%)',
        }}
      />

      {/* Hovered label */}
      {hovered && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 bg-panel border border-bright px-3 py-1 text-xs font-mono text-cyan tracking-wider pointer-events-none">
          ◈ {hovered}
        </div>
      )}

      <GlobeGL
        ref={globeRef}
        width={dims.w || undefined}
        height={dims.h || undefined}

        // Textures
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"

        // Atmosphere
        showAtmosphere
        atmosphereColor="rgba(30,140,255,0.22)"
        atmosphereAltitude={0.13}

        // Country polygons
        polygonsData={filteredPolygons}
        polygonCapColor={polygonCapFn}
        polygonAltitude={0.006}
        polygonSideColor={() => 'rgba(0,0,0,0)'}
        polygonStrokeColor={() => 'rgba(120,180,220,0.25)'}

        // Missile arcs
        arcsData={arcsData}
        arcColor="color"
        arcDashLength={0.45}
        arcDashGap={0.25}
        arcDashAnimateTime={1800}
        arcStroke={0.9}
        arcAltitudeAutoScale={0.38}

        // Conflict markers
        pointsData={CONFLICT_LOCATIONS}
        pointColor={pointColorFn}
        pointAltitude={0.025}
        pointRadius={(d: any) => (d.severity === 'critical' ? 0.45 : d.severity === 'high' ? 0.35 : 0.25)}
        pointResolution={8}
        onPointClick={(pt: any) => { onLocationClick?.(pt.name); }}
        onPointHover={(pt: any) => setHovered(pt?.name ?? null)}

        // Radar rings
        ringsData={ringsData}
        ringColor={ringColorFn}
        ringMaxRadius={3.2}
        ringPropagationSpeed={2.5}
        ringRepeatPeriod={1100}

        // Labels
        labelsData={CONFLICT_LOCATIONS.filter(l => l.severity !== 'low')}
        labelText="name"
        labelColor={labelColorFn}
        labelSize={0.45}
        labelDotRadius={0.22}
        labelAltitude={0.03}
        labelResolution={2}
      />
    </div>
  );
}
