"use client";

import React, { useState, useEffect } from "react";
import { ScoreRadarChart } from "@/components/ScoreRadarChart";
import { StatusBadge } from "@/components/StatusBadge";
import { ActivityHeatmap } from "@/components/ActivityHeatmap";
import { MetricCard } from "@/components/MetricCard";

export default function EvaluationDetailPage({ params }: { params: { id: string } }) {
  const [status, setStatus] = useState<"active" | "locked">("locked");

  const metrics = {
    consistency: { normalized: 88.5, weight: 0.2 },
    pr_quality: { normalized: 92.0, weight: 0.25 },
    review_cycles: { normalized: 95.0, weight: 0.2 },
    collaboration: { normalized: 78.0, weight: 0.15 },
    stability: { normalized: 90.0, weight: 0.2 },
  };

  useEffect(() => {
    if (status === "active") {
      const timer = setInterval(() => {
        console.log("Polling live score from /evaluations/" + params.id + "/score");
      }, 60000);
      return () => clearInterval(timer);
    }
  }, [status, params.id]);

  return (
    <div className="min-h-screen bg-canvas text-ink p-12 font-sans relative overflow-hidden">
      {/* Background Orbs */}
      <div className="absolute top-12 left-10 w-96 h-96 rounded-full gradient-orb-mint pointer-events-none opacity-40"></div>
      <div className="absolute bottom-10 right-10 w-96 h-96 rounded-full gradient-orb-rose pointer-events-none opacity-40"></div>

      <div className="max-w-6xl mx-auto space-y-12 relative z-10">
        {/* Editorial Navigation Header */}
        <div className="flex justify-between items-start border-b border-hairline pb-8">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-5xl font-serif font-light text-ink tracking-tight">Jane Doe</h1>
              <StatusBadge status={status} />
              <button
                onClick={() => setStatus(status === "active" ? "locked" : "active")}
                className="text-[11px] text-muted underline ml-2 uppercase tracking-[0.96px]"
              >
                (Toggle: {status})
              </button>
            </div>
            <p className="text-body text-sm mt-2">
              Repository: <span className="font-mono text-ink font-medium">acme/takehome-backend</span>
            </p>
            <p className="text-xs text-muted mt-1">
              Evaluation Window: July 1, 2026 – July 10, 2026 (Window-bounded sync)
            </p>
          </div>
          <div>
            {status === "locked" ? (
              <a
                href={`/evaluations/${params.id}/report`}
                className="px-6 py-3 bg-ink hover:bg-ink-primary text-on-primary rounded-pill text-xs font-semibold uppercase tracking-[0.96px] transition shadow-soft"
              >
                Download Report Card (PDF)
              </a>
            ) : (
              <span className="text-xs text-ink font-medium uppercase tracking-[0.96px] flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-ink animate-ping"></span> Live Background Syncing
              </span>
            )}
          </div>
        </div>

        {/* ACTIVE STATE VIEW */}
        {status === "active" && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-surface-card border border-hairline rounded-xl p-8 shadow-soft flex flex-col justify-between">
                <div>
                  <span className="text-[12px] uppercase tracking-[0.96px] font-semibold text-muted">
                    In-Progress Live Score
                  </span>
                  <div className="text-6xl font-serif font-light text-ink tracking-tight mt-3">
                    84.20
                  </div>
                </div>
                <p className="text-xs text-muted mt-6">
                  Polling every 60s. Rate-limit-safe GraphQL worker running in background.
                </p>
              </div>

              <div className="md:col-span-2">
                <ActivityHeatmap startDate="2026-07-01" endDate="2026-07-10" />
              </div>
            </div>

            <div className="bg-surface-card border border-hairline rounded-xl p-6 space-y-3 shadow-soft">
              <h4 className="text-[12px] uppercase tracking-[0.96px] font-semibold text-muted">
                Live Activity Ticker
              </h4>
              <ul className="text-xs text-body space-y-2 font-mono">
                <li>• [2026-07-27 04:12] Commit: Add GraphQL query pagination support (+45/-12)</li>
                <li>• [2026-07-27 03:50] Opened PR #4: Implement scoring engine functional core</li>
              </ul>
            </div>
          </div>
        )}

        {/* LOCKED STATE VIEW */}
        {status === "locked" && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-surface-dark text-on-dark rounded-xxl p-8 shadow-2xl flex flex-col justify-between relative overflow-hidden">
                <div>
                  <span className="text-[12px] uppercase tracking-[0.96px] font-semibold text-on-dark-soft">
                    Final Weighted Score
                  </span>
                  <div className="text-7xl font-serif font-light text-on-dark tracking-tight mt-4">
                    89.45
                  </div>
                </div>
                <div className="text-xs text-on-dark-soft mt-8 flex items-center gap-1.5 font-sans">
                  ✓ Score locked into immutable PostgreSQL ledger
                </div>
              </div>

              <div className="md:col-span-2">
                <ScoreRadarChart metrics={metrics} />
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <MetricCard title="Consistency" score={metrics.consistency.normalized} weight={metrics.consistency.weight} />
              <MetricCard title="PR Quality" score={metrics.pr_quality.normalized} weight={metrics.pr_quality.weight} />
              <MetricCard title="Review Cycles" score={metrics.review_cycles.normalized} weight={metrics.review_cycles.weight} />
              <MetricCard title="Collaboration" score={metrics.collaboration.normalized} weight={metrics.collaboration.weight} />
              <MetricCard title="Stability" score={metrics.stability.normalized} weight={metrics.stability.weight} />
            </div>

            {/* Flagged Audit Callouts */}
            <div className="bg-surface-card border border-hairline rounded-xl p-8 shadow-soft space-y-4">
              <h3 className="text-[12px] uppercase tracking-[0.96px] font-semibold text-muted">
                Auditable Scoring Callouts & Risk Flags
              </h3>
              <ul className="space-y-3 text-sm text-body">
                <li className="flex items-center gap-3">
                  <span className="text-ink font-semibold">✓</span> High consistency: Candidate active 8 out of 10 evaluation window days.
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-ink font-semibold">⚠️</span> Commit concentration penalty: 62% of commits occurred in final 10% window.
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
