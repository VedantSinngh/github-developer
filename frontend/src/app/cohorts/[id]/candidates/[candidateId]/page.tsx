"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import RadarChart from "@/components/RadarChart";
import { Skeleton } from "@/components/ui/skeleton";

type ReportData = {
  evaluation_id: number;
  status: string;
  final_score: number | null;
  metrics: {
    [key: string]: {
      raw: number;
      normalized: number;
      weight: number;
    }
  }
};

type EvidenceData = {
  prs: { id: number; title: string; url: string; merged_at: string | null }[];
  commits: { id: number; message: string; url: string; date: string }[];
};

export default function CandidateReportPage() {
  const { id, candidateId } = useParams();
  const [report, setReport] = useState<ReportData | null>(null);
  const [evidence, setEvidence] = useState<EvidenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    
    Promise.all([
      fetch(`${API_URL}/cohorts/${id}/candidates/${candidateId}/report`, { headers: { Authorization: `Bearer ${token}` } }),
      fetch(`${API_URL}/cohorts/${id}/candidates/${candidateId}/evidence`, { headers: { Authorization: `Bearer ${token}` } })
    ])
    .then(async ([repRes, eviRes]) => {
      if (!repRes.ok || !eviRes.ok) throw new Error("Failed to load data");
      const repData = await repRes.json();
      const eviData = await eviRes.json();
      setReport(repData);
      setEvidence(eviData);
    })
    .catch((err) => setError(err.message))
    .finally(() => setLoading(false));

  }, [id, candidateId]);

  if (loading) {
    return <div className="p-12"><Skeleton className="h-64 w-full" /></div>;
  }

  if (error || !report) {
    return <div className="p-12 text-red-600">{error || "No report found"}</div>;
  }

  return (
    <div className="py-section bg-canvas min-h-screen text-ink font-sans">
      <div className="max-w-5xl mx-auto px-6 space-y-12">
        <header className="border-b border-hairline pb-4 flex justify-between items-end">
          <div>
            <h1 className="text-display-sm font-serif font-light tracking-tight">Candidate Report Card</h1>
            <p className="text-muted mt-2 font-mono text-sm">Evaluation #{report.evaluation_id} • Status: <span className="uppercase text-ink font-bold">{report.status}</span></p>
          </div>
          <div className="text-right">
            <p className="text-caption-uppercase text-muted">Final Score</p>
            <p className="text-display-md font-serif text-primary">
              {report.final_score !== null ? report.final_score.toFixed(2) : "—"}
            </p>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="bg-surface-card p-6 border border-hairline rounded-xl shadow-soft">
            <h2 className="text-heading-sm font-serif mb-6">Performance Radar</h2>
            <RadarChart metrics={report.metrics} />
          </div>
          
          <div className="bg-surface-card p-6 border border-hairline rounded-xl shadow-soft">
            <h2 className="text-heading-sm font-serif mb-6">Signal Breakdown</h2>
            <div className="space-y-4">
              {Object.entries(report.metrics).map(([key, data]) => (
                <div key={key} className="flex justify-between items-center border-b border-hairline-soft pb-2 last:border-0">
                  <div>
                    <p className="text-body font-medium capitalize">{key.replace("_", " ")}</p>
                    <p className="text-caption text-muted">Weight: {(data.weight * 100).toFixed(0)}%</p>
                  </div>
                  <div className="text-right">
                    <p className="text-body font-mono">{data.normalized.toFixed(1)} <span className="text-muted text-xs">/ 100</span></p>
                    <p className="text-caption text-muted font-mono" title="Raw value">{data.raw.toFixed(2)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-surface-card p-6 border border-hairline rounded-xl shadow-soft">
          <h2 className="text-heading-sm font-serif mb-6">Evidence Logs</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-body font-bold mb-4">Pull Requests</h3>
              {evidence?.prs.length ? (
                <ul className="space-y-3">
                  {evidence.prs.map(pr => (
                    <li key={pr.id} className="text-sm">
                      <a href={pr.url} target="_blank" rel="noreferrer" className="text-primary hover:underline">{pr.title}</a>
                      <span className="text-muted ml-2">{pr.merged_at ? "Merged" : "Closed/Open"}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted">No PRs found.</p>
              )}
            </div>
            <div>
              <h3 className="text-body font-bold mb-4">Commits</h3>
              {evidence?.commits.length ? (
                <ul className="space-y-3">
                  {evidence.commits.slice(0, 10).map(c => (
                    <li key={c.id} className="text-sm">
                      <a href={c.url} target="_blank" rel="noreferrer" className="text-primary hover:underline truncate inline-block max-w-[200px] align-bottom">
                        {c.message}
                      </a>
                      <span className="text-muted ml-2">{new Date(c.date).toLocaleDateString()}</span>
                    </li>
                  ))}
                  {evidence.commits.length > 10 && <li className="text-sm text-muted">...and {evidence.commits.length - 10} more</li>}
                </ul>
              ) : (
                <p className="text-sm text-muted">No commits found.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
