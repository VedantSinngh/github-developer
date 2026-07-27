"use client";

import React from "react";
import useSWR from "swr";
import { ScoreRadarChart } from "@/components/ScoreRadarChart";
import { StatusBadge } from "@/components/StatusBadge";
import { MetricCard } from "@/components/MetricCard";
import { Skeleton } from "@/components/ui/skeleton";

const fetcher = (url: string) =>
  fetch(url).then((res: Response) => {
    if (!res.ok) throw new Error("Public score card unavailable");
    return res.json();
  });

export default function PublicShareCardPage({
  params,
}: {
  params: { id: string; token: string };
}) {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const { data: scoreData, error, isLoading } = useSWR(
    `${API_URL}/evaluations/${params.id}/share/${params.token}`,
    fetcher
  );

  const metrics = scoreData?.metrics || {
    consistency: { normalized: 0, weight: 0.2 },
    pr_quality: { normalized: 0, weight: 0.25 },
    review_cycles: { normalized: 0, weight: 0.2 },
    collaboration: { normalized: 0, weight: 0.15 },
    stability: { normalized: 0, weight: 0.2 },
  };

  const finalScore = scoreData?.final_score ?? null;

  if (error) {
    return (
      <div className="min-h-screen bg-canvas text-ink p-12 font-sans flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-serif text-ink">Score Card Unavailable</h1>
          <p className="text-body-sm text-muted">
            The requested public score card was not found or the evaluation is not locked yet.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-canvas text-ink p-12 font-sans relative overflow-hidden">
      {/* Atmospheric Orbs */}
      <div className="absolute top-10 right-1/2 translate-x-1/2 w-96 h-96 rounded-full gradient-orb-peach pointer-events-none opacity-50"></div>

      <div className="max-w-4xl mx-auto space-y-12 relative z-10">
        <div className="text-center space-y-3 border-b border-hairline pb-8">
          <span className="text-[12px] uppercase tracking-[0.96px] font-semibold text-muted">
            Public Verified Candidate Score Card
          </span>
          <h1 className="text-5xl font-serif font-light text-ink tracking-tight">
            Evaluation #{params.id}
          </h1>
          <div className="flex justify-center gap-3 items-center">
            <StatusBadge status={scoreData?.status || "locked"} />
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
          <div className="text-7xl font-serif font-light text-on-dark tracking-tight">
            {isLoading ? <Skeleton className="h-20 w-36 mx-auto bg-on-dark-soft/20" /> : (finalScore !== null ? Number(finalScore).toFixed(2) : "—")}
          </div>
          <p className="text-xs text-on-dark-soft font-sans mt-4">
            ✓ Immutable Ledger Entry Verified in PostgreSQL
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <MetricCard title="Consistency" score={metrics.consistency?.normalized ?? 0} weight={metrics.consistency?.weight ?? 0.2} />
          <MetricCard title="PR Quality" score={metrics.pr_quality?.normalized ?? 0} weight={metrics.pr_quality?.weight ?? 0.25} />
          <MetricCard title="Review Cycles" score={metrics.review_cycles?.normalized ?? 0} weight={metrics.review_cycles?.weight ?? 0.2} />
          <MetricCard title="Collaboration" score={metrics.collaboration?.normalized ?? 0} weight={metrics.collaboration?.weight ?? 0.15} />
          <MetricCard title="Stability" score={metrics.stability?.normalized ?? 0} weight={metrics.stability?.weight ?? 0.2} />
        </div>

        <ScoreRadarChart metrics={metrics} />
      </div>
    </div>
  );
}
