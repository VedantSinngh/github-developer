"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

type LeaderboardEntry = {
  candidate_id: number;
  name: string;
  email: string;
  github_username: string;
  status: string;
  final_score: number | null;
};

export default function CohortDashboardPage() {
  const { id } = useParams();
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchLeaderboard = () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${API_URL}/cohorts/${id}/leaderboard`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch leaderboard");
        return res.json();
      })
      .then((data) => {
        setLeaderboard(data.leaderboard);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLeaderboard();
  }, [id]);

  const handleStartCohort = async () => {
    setStarting(true);
    setError(null);
    setSuccessMsg(null);
    const token = localStorage.getItem("token");
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${API_URL}/cohorts/${id}/start`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to start cohort");
      }
      setSuccessMsg("Cohort started! Repositories are being forked in the background.");
      fetchLeaderboard(); // Refresh to see statuses update
    } catch (err: any) {
      setError(err.message);
    } finally {
      setStarting(false);
    }
  };

  return (
    <div className="py-section bg-canvas text-ink font-sans relative min-h-screen">
      <div className="max-w-7xl mx-auto px-6 md:px-12 space-y-8 relative z-10">
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-hairline pb-8">
          <div className="space-y-4">
            <h1 className="text-display-lg font-serif font-light text-ink tracking-tight">
              Cohort Dashboard
            </h1>
          </div>
          <button
            onClick={handleStartCohort}
            disabled={starting}
            className="inline-flex h-10 items-center justify-center rounded-pill bg-primary px-5 text-button text-on-primary hover:bg-primary-active transition-colors disabled:opacity-50"
          >
            {starting ? "Starting..." : "Start Cohort"}
          </button>
        </header>

        {error && <div className="p-4 bg-red-100 text-red-800 rounded-md">{error}</div>}
        {successMsg && <div className="p-4 bg-green-100 text-green-800 rounded-md">{successMsg}</div>}

        <div className="bg-surface-card border border-hairline rounded-xl shadow-soft">
          <div className="p-6 border-b border-hairline">
            <h2 className="text-heading-sm font-serif">Leaderboard</h2>
          </div>
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : (
            <Table>
              <TableHeader className="bg-canvas-soft text-caption-uppercase text-muted border-b border-hairline">
                <TableRow>
                  <TableHead className="p-6 font-medium">Rank</TableHead>
                  <TableHead className="p-6 font-medium">Candidate</TableHead>
                  <TableHead className="p-6 font-medium">GitHub</TableHead>
                  <TableHead className="p-6 font-medium">Status</TableHead>
                  <TableHead className="p-6 font-medium">Score</TableHead>
                  <TableHead className="p-6 text-right font-medium">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className="divide-y divide-hairline-soft">
                {leaderboard.map((entry: LeaderboardEntry, idx) => (
                  <TableRow key={entry.candidate_id} className="hover:bg-canvas-soft transition-colors">
                    <TableCell className="p-6 font-mono text-xl">{idx + 1}</TableCell>
                    <TableCell className="p-6 font-serif font-light text-xl text-ink tracking-tight">{entry.name}</TableCell>
                    <TableCell className="p-6 text-body-sm text-muted">@{entry.github_username}</TableCell>
                    <TableCell className="p-6 text-sm">{entry.status}</TableCell>
                    <TableCell className="p-6 font-serif font-light text-2xl text-ink tracking-tight">
                      {entry.final_score !== null ? entry.final_score.toFixed(2) : "—"}
                    </TableCell>
                    <TableCell className="p-6 text-right">
                      <a
                        href={`/cohorts/${id}/candidates/${entry.candidate_id}`}
                        className="text-caption-uppercase text-ink hover:underline font-bold"
                      >
                        View Report →
                      </a>
                    </TableCell>
                  </TableRow>
                ))}
                {leaderboard.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="p-6 text-center text-muted">
                      No candidates in this cohort yet.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </div>
      </div>
    </div>
  );
}
