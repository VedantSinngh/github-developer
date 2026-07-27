"use client";

import React, { useState, useEffect } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

type Evaluation = {
  id: number;
  candidate: string;
  repo: string;
  status: string;
  score: number | null;
};

export default function DashboardPage() {
  const [filter, setFilter] = useState<string>("all");

  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${API_URL}/evaluations`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch evaluations");
        return res.json();
      })
      .then((data) => {
        const mapped = data.map((item: any) => ({
          id: item.id,
          candidate: item.candidate_name,
          repo: `${item.repo_owner}/${item.repo_name}`,
          status: item.status,
          score: item.final_score ? parseFloat(item.final_score) : null,
        }));
        setEvaluations(mapped);
      })
      .catch((err) => console.error("Error fetching evaluations:", err))
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter === "all" ? evaluations : evaluations.filter((e: Evaluation) => e.status === filter);

  return (
    <div className="py-section bg-canvas text-ink font-sans relative overflow-hidden">
      {/* Background Atmosphere Orbs */}
      <div className="absolute top-1/4 right-1/4 w-[600px] h-[600px] rounded-full gradient-orb-peach pointer-events-none opacity-40 mix-blend-multiply blur-3xl z-0"></div>
      <div className="absolute bottom-1/4 left-1/4 w-[600px] h-[600px] rounded-full gradient-orb-sky pointer-events-none opacity-40 mix-blend-multiply blur-3xl z-0"></div>

      <div className="max-w-7xl mx-auto px-6 md:px-12 space-y-12 relative z-10">
        {/* Editorial Top Navigation */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-hairline pb-8">
          <div className="space-y-4">
            <span className="text-caption-uppercase text-muted">
              ElevenLabs Editorial Platform
            </span>
            <h1 className="text-display-lg font-serif font-light text-ink tracking-tight mt-1">
              Evaluations Index
            </h1>
          </div>
          <a
            href="/evaluations/new"
            className="inline-flex h-10 items-center justify-center rounded-pill bg-primary px-5 text-button text-on-primary hover:bg-primary-active transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink"
          >
            + Create New Evaluation
          </a>
        </header>

        {/* Status Filter Pills */}
        <div className="flex gap-3 border-b border-hairline-soft pb-4 overflow-x-auto">
          {["all", "pending", "active", "completed", "locked"].map((st) => (
            <button
              key={st}
              onClick={() => setFilter(st)}
              className={`px-4 py-1.5 rounded-pill text-caption-uppercase transition-colors whitespace-nowrap ${
                filter === st
                  ? "bg-ink text-on-primary"
                  : "bg-surface-strong text-muted hover:text-ink hover:bg-canvas-soft"
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Minimalist Editorial Table */}
        <div className="bg-surface-card border border-hairline rounded-xl shadow-soft">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : (
            <Table>
              <TableHeader className="bg-canvas-soft text-caption-uppercase text-muted border-b border-hairline">
                <TableRow>
                  <TableHead className="p-6 font-medium">Candidate</TableHead>
                  <TableHead className="p-6 font-medium">Repository</TableHead>
                  <TableHead className="p-6 font-medium">Status</TableHead>
                  <TableHead className="p-6 font-medium">Final Score</TableHead>
                  <TableHead className="p-6 text-right font-medium">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className="divide-y divide-hairline-soft">
                {filtered.map((ev: Evaluation) => (
                  <TableRow key={ev.id} className="hover:bg-canvas-soft transition-colors">
                    <TableCell className="p-6 font-serif font-light text-2xl text-ink tracking-tight">{ev.candidate}</TableCell>
                    <TableCell className="p-6 text-body-sm text-body font-mono">{ev.repo}</TableCell>
                    <TableCell className="p-6">
                      <StatusBadge status={ev.status} />
                    </TableCell>
                    <TableCell className="p-6 font-serif font-light text-3xl text-ink tracking-tight">
                      {ev.score !== null ? ev.score.toFixed(2) : "—"}
                    </TableCell>
                    <TableCell className="p-6 text-right">
                      <a
                        href={`/evaluations/${ev.id}`}
                        className="text-caption-uppercase text-ink hover:underline"
                      >
                        View Report →
                      </a>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </div>
    </div>
  );
}
