import React from "react";

interface MetricCardProps {
  title: string;
  score: number;
  weight: number;
  subtitle?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({ title, score, weight, subtitle }) => {
  return (
    <div className="bg-surface-card border border-hairline rounded-xl p-6 shadow-soft hover:border-hairline-strong transition flex flex-col justify-between">
      <div className="flex justify-between items-start">
        <h4 className="text-[12px] uppercase tracking-[0.96px] font-semibold text-muted">
          {title}
        </h4>
        <span className="text-[11px] font-sans text-muted-soft bg-surface-strong px-2 py-0.5 rounded-pill">
          w: {(weight * 100).toFixed(0)}%
        </span>
      </div>
      <div className="mt-6">
        <div className="text-4xl font-serif font-light text-ink tracking-tight">
          {score.toFixed(1)}
        </div>
        {subtitle && <p className="text-xs text-muted mt-1.5">{subtitle}</p>}
      </div>
    </div>
  );
};
