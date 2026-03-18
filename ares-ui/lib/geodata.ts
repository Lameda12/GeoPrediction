import type { ConflictLocation, MissileArc } from './types';

export const CONFLICT_LOCATIONS: ConflictLocation[] = [
  { lat: 33.7245, lng: 51.7270, name: 'Natanz Nuclear',      type: 'nuclear_target', active: true,  severity: 'critical' },
  { lat: 34.8847, lng: 49.1233, name: 'Fordow Facility',     type: 'nuclear_target', active: true,  severity: 'critical' },
  { lat: 32.4167, lng: 53.6800, name: 'Isfahan Complex',     type: 'nuclear_target', active: true,  severity: 'high'     },
  { lat: 35.6892, lng: 51.3890, name: 'Tehran',              type: 'command',        active: true,  severity: 'high'     },
  { lat: 31.7683, lng: 35.2137, name: 'Jerusalem',           type: 'command',        active: true,  severity: 'moderate' },
  { lat: 32.0853, lng: 34.7818, name: 'Tel Aviv',            type: 'military',       active: true,  severity: 'high'     },
  { lat: 31.2516, lng: 34.7913, name: 'Nevatim AB',          type: 'military',       active: true,  severity: 'high'     },
  { lat: 26.5000, lng: 56.5000, name: 'Strait of Hormuz',    type: 'naval',          active: true,  severity: 'critical' },
  { lat: 33.8938, lng: 35.5018, name: 'Beirut',              type: 'proxy',          active: true,  severity: 'moderate' },
  { lat: 15.3694, lng: 44.1910, name: 'Sanaa',               type: 'proxy',          active: true,  severity: 'moderate' },
  { lat: 33.3152, lng: 44.3661, name: 'Baghdad',             type: 'proxy',          active: true,  severity: 'moderate' },
  { lat: 26.0667, lng: 50.5577, name: 'Manama (5th Fleet)',  type: 'naval',          active: true,  severity: 'low'      },
  { lat: 38.9072, lng: -77.036, name: 'Washington D.C.',     type: 'command',        active: true,  severity: 'low'      },
  { lat: 36.2021, lng: 37.1343, name: 'Incirlik AB',         type: 'military',       active: false, severity: 'low'      },
];

export const MISSILE_ARCS: MissileArc[] = [
  // Israeli Air Force strikes
  {
    startLat: 31.2516, startLng: 34.7913,
    endLat: 33.7245,   endLng: 51.7270,
    label: 'IAF → Natanz', color: '#ff8c00', actor: 'israel', active: true,
  },
  {
    startLat: 31.2516, startLng: 34.7913,
    endLat: 34.8847,   endLng: 49.1233,
    label: 'IAF → Fordow', color: '#ff8c00', actor: 'israel', active: true,
  },
  {
    startLat: 31.2516, startLng: 34.7913,
    endLat: 32.4167,   endLng: 53.6800,
    label: 'IAF → Isfahan', color: '#ffaa40', actor: 'israel', active: true,
  },
  // Iran ballistic missile retaliation
  {
    startLat: 35.6892, startLng: 51.3890,
    endLat: 32.0853,   endLng: 34.7818,
    label: 'IRGC Ballistic → Tel Aviv', color: '#ff2020', actor: 'iran', active: true,
  },
  {
    startLat: 35.6892, startLng: 51.3890,
    endLat: 31.7683,   endLng: 35.2137,
    label: 'IRGC Ballistic → Jerusalem', color: '#ff2020', actor: 'iran', active: true,
  },
  // Hezbollah barrage
  {
    startLat: 33.8938, startLng: 35.5018,
    endLat: 32.9000,   endLng: 35.3000,
    label: 'Hezbollah → N. Israel', color: '#ff5500', actor: 'hezbollah', active: true,
  },
  // Houthi Red Sea missile
  {
    startLat: 15.3694, startLng: 44.1910,
    endLat: 29.5000,   endLng: 34.9000,
    label: 'Houthi → Red Sea / Eilat', color: '#bb4400', actor: 'houthis', active: true,
  },
  // US CENTCOM carrier strike (conditional)
  {
    startLat: 21.5000, startLng: 59.5000,
    endLat: 30.0000,   endLng: 48.0000,
    label: 'USS Carrier Strike', color: '#00ccff', actor: 'usa', active: false,
  },
];

// Countries to highlight on the globe
export const COUNTRIES_OF_INTEREST: string[] = [
  'United States of America',
  'Israel', 'Iran',
  'Lebanon', 'Yemen',
  'Saudi Arabia', 'Iraq',
  'Russia', 'China', 'Bahrain',
];

export const COUNTRY_COLORS: Record<string, string> = {
  'United States of America': 'rgba(0, 150, 255, 0.25)',
  'Israel':                   'rgba(255, 140, 0, 0.38)',
  'Iran':                     'rgba(255, 32, 32, 0.38)',
  'Lebanon':                  'rgba(255, 80, 20, 0.28)',
  'Yemen':                    'rgba(200, 60, 0, 0.26)',
  'Saudi Arabia':             'rgba(180, 100, 0, 0.22)',
  'Iraq':                     'rgba(180, 60, 0, 0.22)',
  'Russia':                   'rgba(0, 80, 160, 0.22)',
  'China':                    'rgba(160, 0, 0, 0.22)',
  'Bahrain':                  'rgba(0, 120, 200, 0.22)',
};

export const SEVERITY_RING_COLOR: Record<string, string> = {
  critical: '255, 32, 32',
  high:     '255, 140, 0',
  moderate: '255, 200, 0',
  low:      '0, 200, 255',
};
