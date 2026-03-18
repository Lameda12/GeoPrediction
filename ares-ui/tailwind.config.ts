import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        base:    '#000205',
        surface: '#050d1a',
        panel:   '#080f1e',
        border:  '#0e2d4a',
        bright:  '#1a5f8a',
        text:    '#a8d8ea',
        dim:     '#4a7a8f',
        amber:   '#ff8c00',
        red:     '#ff2020',
        green:   '#00cc66',
        cyan:    '#00ccff',
      },
      fontFamily: { mono: ['JetBrains Mono', 'Fira Code', 'monospace'] },
      animation: {
        pulse2:   'pulse 2s cubic-bezier(0.4,0,0.6,1) infinite',
        scanline: 'scanline 8s linear infinite',
        flicker:  'flicker 4s linear infinite',
        glow:     'glow 2s ease-in-out infinite alternate',
        'count-up': 'countUp 0.8s ease-out forwards',
      },
      keyframes: {
        scanline: {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        flicker: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.97' },
          '92%':      { opacity: '0.95' },
          '93%':      { opacity: '0.99' },
        },
        glow: {
          from: { textShadow: '0 0 4px currentColor' },
          to:   { textShadow: '0 0 12px currentColor, 0 0 20px currentColor' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
