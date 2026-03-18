import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title:       'ARES — Adaptive Risk & Escalation Simulator',
  description: 'Research-grade geopolitical conflict simulation engine. [MODEL OUTPUT — NOT PREDICTIVE INTELLIGENCE]',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
