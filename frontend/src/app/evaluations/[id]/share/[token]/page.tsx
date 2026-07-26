"use client";

import React from "react";
import { ScoreRadarChart } from "@/components/ScoreRadarChart";
import { StatusBadge } from "@/components/StatusBadge";
import { MetricCard } from "@/components/MetricCard";

export default function PublicShareCardPage({
  params,
}: {
  params: { id: string; token: string };
}) {
  const sampleMetrics = {
    consistency: { normalized: 88.5, weight: 0.2 },
    pr_quality: { normalized: 92.0, weight: 0.25 },
    review_cycles: { normalized: 95.0, weight: 0.2 },
    collaboration: { normalized: 78.0, weight: 0.15 },
    stability: { normalized: 90.0, weight: 0.2 },
  };

  return (
    <div className="min-h-screen bg-canvas text-ink p-12 font-sans relative overflow-hidden">
      {/* Atmospheric Orbs */}
      <div className="absolute top-10 right-1/2 translate-x-1/2 w-96 h-96 rounded-full gradient-orb-peach pointer-events-none opacity-50"></div>

      <div className="max-w-4xl mx-auto space-y-12 relative z-10">
        <div className="text-center space-y-3 border-b border-hairline pb-8">
          <span className="text-[12px] uppercase tracking-[0.96px] font-semibold text-muted">
            Public Verified Candidate Score Card
          </span>
          <h1 className="text-5xl font-serif font-light text-ink tracking-tight">Jane Doe</h1>
          <div className="flex justify-center gap-3 items-center">
            <StatusBadge status="locked" />
            <span className="text-xs text-muted font-mono">
              Token: {params.token.slice(0, 8)}...
            </span>
          </div>
        </div>

        {/* Hero Score Card */}
        <div className="bg-surface-dark text-on-dark rounded-xxl p-10 text-center space-y-3 shadow-2xl relative overflow-hidden">
          <span className="text-[12px] uppercase tracking-[0.96px] font-semibold text-on-dark-soft">
            Verified Final Score
          </span>
          <div className="text-7xl font-serif font-light text-on-dark tracking-tight">89.45</div>
          <p className="text-xs text-on-dark-soft font-sans mt-4">
            ✓ Immutable Ledger Entry Verified in PostgreSQL
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <MetricCard title="Consistency" score={88.5} weight={0.2} />
          <MetricCard title="PR Quality" score={92.0} weight={0.25} />
          <MetricCard title="Review Cycles" score={95.0} weight={0.2} />
          <MetricCard title="Collaboration" score={78.0} weight={0.15} />
          <MetricCard title="Stability" score={90.0} weight={0.2} />
        </div>

        <ScoreRadarChart metrics={sampleMetrics} />
      </div>
    </div>
  );
}
