"use client";

import React, { useState } from "react";
import useSWR from "swr";
import { ScoreRadarChart } from "@/components/ScoreRadarChart";
import { StatusBadge } from "@/components/StatusBadge";
import { ActivityHeatmap } from "@/components/ActivityHeatmap";
import { MetricCard } from "@/components/MetricCard";
import { Skeleton } from "@/components/ui/skeleton";

const fetcher = (url: string) => {
  const token = localStorage.getItem("token");
  return fetch(url, { headers: { Authorization: `Bearer ${token}` } }).then((res: Response) => res.json());
};

export default function EvaluationDetailPage({ params }: { params: { id: string } }) {
  const [status, setStatus] = useState<"active" | "locked">("locked");

  const { data: scoreData, error, isLoading } = useSWR(
    `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/evaluations/${params.id}/score`,
    fetcher,
    { refreshInterval: status === "active" ? 15000 : 0 } // Poll every 15s if active
  );

  // Derive status from API if available, else fallback to state
  const currentStatus = scoreData?.status || status;

  const fallbackMetrics = {
    consistency: { normalized: 88.5, weight: 0.2 },
    pr_quality: { normalized: 92.0, weight: 0.25 },
    review_cycles: { normalized: 95.0, weight: 0.2 },
    collaboration: { normalized: 78.0, weight: 0.15 },
    stability: { normalized: 90.0, weight: 0.2 },
  };

  const currentMetrics = scoreData?.breakdown ? {
    consistency: { normalized: scoreData.breakdown.consistency_score, weight: 0.2 },
    pr_quality: { normalized: scoreData.breakdown.pr_quality_score, weight: 0.25 },
    review_cycles: { normalized: scoreData.breakdown.review_cycles_score, weight: 0.2 },
    collaboration: { normalized: scoreData.breakdown.collaboration_score, weight: 0.15 },
    stability: { normalized: scoreData.breakdown.stability_score, weight: 0.2 },
  } : fallbackMetrics;

  const finalScore = scoreData?.final_score ?? null;

  return (
    <div className="py-section px-6 md:px-12 bg-canvas text-ink font-sans relative overflow-hidden">
      {/* Background Orbs */}
      <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] rounded-full gradient-orb-mint pointer-events-none opacity-40 mix-blend-multiply blur-3xl z-0"></div>
      <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] rounded-full gradient-orb-rose pointer-events-none opacity-40 mix-blend-multiply blur-3xl z-0"></div>

      <div className="max-w-7xl mx-auto space-y-12 relative z-10">
        {/* Editorial Navigation Header */}
        <div className="flex flex-col md:flex-row justify-between items-start border-b border-hairline pb-8 gap-6">
          <div>
            <div className="flex items-center gap-4">
              <h1 className="text-display-xl font-serif font-light text-ink tracking-tight">Jane Doe</h1>
              <StatusBadge status={currentStatus} />
              <button
                onClick={() => setStatus(status === "active" ? "locked" : "active")}
                className="text-caption-uppercase text-muted underline ml-2 hover:text-ink transition-colors"
              >
                (Mock Toggle: {currentStatus})
              </button>
            </div>
            <p className="text-body-sm text-body mt-4">
              Repository: <span className="font-mono text-ink font-medium">acme/takehome-backend</span>
            </p>
            <p className="text-caption text-muted mt-1">
              Evaluation Window: July 1, 2026 – July 10, 2026 (Window-bounded sync)
            </p>
          </div>
          <div>
            {currentStatus === "locked" ? (
              <a
                href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/evaluations/${params.id}/report`}
                target="_blank"
                className="inline-flex h-10 items-center justify-center rounded-pill bg-primary px-5 text-button text-on-primary hover:bg-primary-active transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink"
              >
                Download Report Card (PDF)
              </a>
            ) : (
              <span className="text-caption-uppercase text-ink font-medium flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-ink animate-ping"></span> Live Background Syncing
              </span>
            )}
          </div>
        </div>

        {/* ACTIVE STATE VIEW */}
        {currentStatus === "active" && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-surface-card border border-hairline rounded-xl p-8 shadow-soft flex flex-col justify-between">
                <div>
                  <span className="text-caption-uppercase text-muted">
                    In-Progress Live Score
                  </span>
                  <div className="text-display-xl font-serif font-light text-ink tracking-tight mt-4">
                    {isLoading ? <Skeleton className="h-16 w-32" /> : (finalScore !== null ? finalScore.toFixed(2) : "—")}
                  </div>
                </div>
                <p className="text-caption text-muted mt-6">
                  Polling every 15s. Rate-limit-safe GraphQL worker running in background.
                </p>
              </div>

              <div className="md:col-span-2">
                <ActivityHeatmap startDate="2026-07-01" endDate="2026-07-10" />
              </div>
            </div>

            <div className="bg-surface-card border border-hairline rounded-xl p-6 space-y-4 shadow-soft">
              <h4 className="text-caption-uppercase text-muted">
                Live Activity Ticker
              </h4>
              <ul className="text-body-sm text-body space-y-3 font-mono">
                <li>• [2026-07-27 04:12] Commit: Add GraphQL query pagination support (+45/-12)</li>
                <li>• [2026-07-27 03:50] Opened PR #4: Implement scoring engine functional core</li>
              </ul>
            </div>
          </div>
        )}

        {/* LOCKED STATE VIEW */}
        {currentStatus === "locked" && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-surface-dark text-on-dark rounded-xxl p-8 shadow-2xl flex flex-col justify-between relative overflow-hidden">
                <div>
                  <span className="text-caption-uppercase text-on-dark-soft">
                    Final Weighted Score
                  </span>
                  <div className="text-display-mega font-serif font-light text-on-dark tracking-tight mt-6">
                    {isLoading ? <Skeleton className="h-20 w-32 bg-on-dark-soft/20" /> : (finalScore !== null ? finalScore.toFixed(2) : "—")}
                  </div>
                </div>
                <div className="text-body-sm text-on-dark-soft mt-8 flex items-center gap-2 font-sans">
                  <span className="text-semantic-success">✓</span> Score locked into immutable PostgreSQL ledger
                </div>
              </div>

              <div className="md:col-span-2">
                <ScoreRadarChart metrics={currentMetrics} />
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <MetricCard title="Consistency" score={currentMetrics.consistency.normalized} weight={currentMetrics.consistency.weight} />
              <MetricCard title="PR Quality" score={currentMetrics.pr_quality.normalized} weight={currentMetrics.pr_quality.weight} />
              <MetricCard title="Review Cycles" score={currentMetrics.review_cycles.normalized} weight={currentMetrics.review_cycles.weight} />
              <MetricCard title="Collaboration" score={currentMetrics.collaboration.normalized} weight={currentMetrics.collaboration.weight} />
              <MetricCard title="Stability" score={currentMetrics.stability.normalized} weight={currentMetrics.stability.weight} />
            </div>

            {/* Flagged Audit Callouts */}
            <div className="bg-surface-card border border-hairline rounded-xl p-8 shadow-soft space-y-6">
              <h3 className="text-caption-uppercase text-muted">
                Auditable Scoring Callouts & Risk Flags
              </h3>
              <ul className="space-y-4 text-body-md text-body">
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
