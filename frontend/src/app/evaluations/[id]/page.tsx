"use client";

import React from "react";
import useSWR from "swr";
import { ScoreRadarChart } from "@/components/ScoreRadarChart";
import { StatusBadge } from "@/components/StatusBadge";
import { ActivityHeatmap } from "@/components/ActivityHeatmap";
import { MetricCard } from "@/components/MetricCard";
import { Skeleton } from "@/components/ui/skeleton";

const fetcher = (url: string) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  return fetch(url, { headers: { Authorization: `Bearer ${token}` } }).then((res: Response) => {
    if (!res.ok) throw new Error("Failed to load data");
    return res.json();
  });
};

type TimelineItem = {
  type: string;
  id: number;
  timestamp: string;
  author: string;
  summary: string;
};

export default function EvaluationDetailPage({ params }: { params: { id: string } }) {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const { data: evalData, error: evalError, isLoading: evalLoading } = useSWR(
    `${API_URL}/evaluations/${params.id}`,
    fetcher
  );

  const currentStatus = evalData?.status || "pending";

  const { data: scoreData, error: scoreError, isLoading: scoreLoading } = useSWR(
    `${API_URL}/evaluations/${params.id}/score`,
    fetcher,
    { refreshInterval: currentStatus === "active" ? 15000 : 0 }
  );

  const { data: timelineData } = useSWR<TimelineItem[]>(
    `${API_URL}/evaluations/${params.id}/timeline`,
    fetcher
  );

  const metrics = scoreData?.metrics || {
    consistency: { normalized: 0, weight: 0.2 },
    pr_quality: { normalized: 0, weight: 0.25 },
    review_cycles: { normalized: 0, weight: 0.2 },
    collaboration: { normalized: 0, weight: 0.15 },
    stability: { normalized: 0, weight: 0.2 },
  };

  const finalScore = scoreData?.final_score ?? evalData?.final_score ?? null;
  const flaggedNotes = scoreData?.flagged_notes || [];

  const startDateFormatted = evalData?.start_date ? new Date(evalData.start_date).toLocaleDateString() : "—";
  const endDateFormatted = evalData?.end_date ? new Date(evalData.end_date).toLocaleDateString() : "—";

  if (evalError) {
    return (
      <div className="py-section px-6 md:px-12 bg-canvas text-ink text-center">
        <p className="text-red-500 font-medium">Failed to load evaluation details.</p>
      </div>
    );
  }

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
              <h1 className="text-display-xl font-serif font-light text-ink tracking-tight">
                {evalLoading ? <Skeleton className="h-12 w-48" /> : (evalData?.candidate_name || "Evaluation")}
              </h1>
              <StatusBadge status={currentStatus} />
            </div>
            <p className="text-body-sm text-body mt-4">
              Repository: <span className="font-mono text-ink font-medium">{evalData ? `${evalData.repo_owner}/${evalData.repo_name}` : "—"}</span>
            </p>
            <p className="text-caption text-muted mt-1">
              Evaluation Window: {startDateFormatted} – {endDateFormatted} (Window-bounded sync)
            </p>
          </div>
          <div>
            {currentStatus === "locked" || currentStatus === "completed" ? (
              <a
                href={`${API_URL}/evaluations/${params.id}/report`}
                target="_blank"
                rel="noreferrer"
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

        {/* ACTIVE / PENDING STATE VIEW */}
        {(currentStatus === "active" || currentStatus === "pending") && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-surface-card border border-hairline rounded-xl p-8 shadow-soft flex flex-col justify-between">
                <div>
                  <span className="text-caption-uppercase text-muted">
                    In-Progress Live Score
                  </span>
                  <div className="text-display-xl font-serif font-light text-ink tracking-tight mt-4">
                    {scoreLoading ? <Skeleton className="h-16 w-32" /> : (finalScore !== null ? Number(finalScore).toFixed(2) : "—")}
                  </div>
                </div>
                <p className="text-caption text-muted mt-6">
                  Polling every 15s. Rate-limit-safe GraphQL worker running in background.
                </p>
              </div>

              <div className="md:col-span-2">
                <ActivityHeatmap
                  startDate={startDateFormatted}
                  endDate={endDateFormatted}
                  activities={timelineData ? timelineData.map(t => ({ date: t.timestamp.split("T")[0], count: 1 })) : []}
                />
              </div>
            </div>

            <div className="bg-surface-card border border-hairline rounded-xl p-6 space-y-4 shadow-soft">
              <h4 className="text-caption-uppercase text-muted">
                Live Activity Ticker
              </h4>
              {timelineData && timelineData.length > 0 ? (
                <ul className="text-body-sm text-body space-y-3 font-mono">
                  {timelineData.map((item) => (
                    <li key={item.id}>• [{new Date(item.timestamp).toLocaleString()}] {item.summary}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-body-sm text-muted font-mono">No repository activity recorded yet in this window.</p>
              )}
            </div>
          </div>
        )}

        {/* LOCKED STATE VIEW */}
        {(currentStatus === "locked" || currentStatus === "completed") && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-surface-dark text-on-dark rounded-xxl p-8 shadow-2xl flex flex-col justify-between relative overflow-hidden">
                <div>
                  <span className="text-caption-uppercase text-on-dark-soft">
                    Final Weighted Score
                  </span>
                  <div className="text-display-mega font-serif font-light text-on-dark tracking-tight mt-6">
                    {scoreLoading ? <Skeleton className="h-20 w-32 bg-on-dark-soft/20" /> : (finalScore !== null ? Number(finalScore).toFixed(2) : "—")}
                  </div>
                </div>
                <div className="text-body-sm text-on-dark-soft mt-8 flex items-center gap-2 font-sans">
                  <span className="text-semantic-success">✓</span> Score locked into immutable PostgreSQL ledger
                </div>
              </div>

              <div className="md:col-span-2">
                <ScoreRadarChart metrics={metrics} />
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <MetricCard title="Consistency" score={metrics.consistency?.normalized ?? 0} weight={metrics.consistency?.weight ?? 0.2} />
              <MetricCard title="PR Quality" score={metrics.pr_quality?.normalized ?? 0} weight={metrics.pr_quality?.weight ?? 0.25} />
              <MetricCard title="Review Cycles" score={metrics.review_cycles?.normalized ?? 0} weight={metrics.review_cycles?.weight ?? 0.2} />
              <MetricCard title="Collaboration" score={metrics.collaboration?.normalized ?? 0} weight={metrics.collaboration?.weight ?? 0.15} />
              <MetricCard title="Stability" score={metrics.stability?.normalized ?? 0} weight={metrics.stability?.weight ?? 0.2} />
            </div>

            {/* Flagged Audit Callouts */}
            <div className="bg-surface-card border border-hairline rounded-xl p-8 shadow-soft space-y-6">
              <h3 className="text-caption-uppercase text-muted">
                Auditable Scoring Callouts & Risk Flags
              </h3>
              {flaggedNotes.length > 0 ? (
                <ul className="space-y-4 text-body-md text-body">
                  {flaggedNotes.map((note: string, idx: number) => (
                    <li key={idx} className="flex items-center gap-3">
                      <span className="text-ink font-semibold">ℹ️</span> {note}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-body-sm text-muted">No high-risk flags identified during evaluation window.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
