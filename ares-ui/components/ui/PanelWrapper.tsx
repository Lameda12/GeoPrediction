'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface Props {
  title:     string;
  subtitle?: string;
  badge?:    string;
  badgeColor?: string;
  children:  ReactNode;
  className?: string;
  noPad?:    boolean;
}

export default function PanelWrapper({ title, subtitle, badge, badgeColor = '#ff8c00', children, className = '', noPad }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`relative bg-panel border border-border flex flex-col ${className}`}
      style={{ boxShadow: 'inset 0 0 24px rgba(0,20,50,0.6)' }}
    >
      {/* Corner decorations */}
      <span className="absolute top-0 left-0 w-3 h-3 border-t border-l border-bright" />
      <span className="absolute top-0 right-0 w-3 h-3 border-t border-r border-bright" />
      <span className="absolute bottom-0 left-0 w-3 h-3 border-b border-l border-bright" />
      <span className="absolute bottom-0 right-0 w-3 h-3 border-b border-r border-bright" />

      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-surface shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-[10px] tracking-[0.22em] font-mono text-dim uppercase">
            {title}
          </span>
          {subtitle && (
            <span className="text-[9px] text-dim/60 font-mono">{subtitle}</span>
          )}
        </div>
        {badge && (
          <span
            className="text-[9px] font-mono px-1.5 py-0.5 border"
            style={{ color: badgeColor, borderColor: badgeColor + '60', background: badgeColor + '12' }}
          >
            {badge}
          </span>
        )}
      </div>

      {/* Content */}
      <div className={`flex-1 min-h-0 overflow-auto ${noPad ? '' : 'p-3'}`}>
        {children}
      </div>
    </motion.div>
  );
}
