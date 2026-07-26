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

export default function DashboardPage() {
  const [filter, setFilter] = useState<string>("all");

  const [evaluations, setEvaluations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In a real app, fetch from GET /evaluations here
    // For now, simulate network delay to show Skeleton
    setTimeout(() => {
      setEvaluations([
        { id: 1, candidate: "Jane Doe", repo: "acme/takehome-backend", status: "locked", score: 89.45 },
        { id: 2, candidate: "John Smith", repo: "acme/live-project", status: "active", score: 76.20 },
        { id: 3, candidate: "Alice Johnson", repo: "acme/frontend-eval", status: "pending", score: null },
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const filtered = filter === "all" ? evaluations : evaluations.filter((e) => e.status === filter);

  return (
    <div className="min-h-screen bg-canvas text-ink p-12 font-sans relative overflow-hidden">
      {/* Background Atmosphere Orbs */}
      <div className="absolute top-10 right-10 w-96 h-96 rounded-full gradient-orb-peach pointer-events-none opacity-50"></div>
      <div className="absolute bottom-10 left-10 w-96 h-96 rounded-full gradient-orb-sky pointer-events-none opacity-50"></div>

      <div className="max-w-6xl mx-auto space-y-12 relative z-10">
        {/* Editorial Top Navigation */}
        <header className="flex justify-between items-center border-b border-hairline pb-8">
          <div>
            <span className="text-[12px] uppercase tracking-[0.96px] font-semibold text-muted">
              ElevenLabs Voice-AI Platform
            </span>
            <h1 className="text-5xl font-serif font-light text-ink tracking-tight mt-1">
              Evaluations Index
            </h1>
          </div>
          <a
            href="/evaluations/new"
            className="px-6 py-3 bg-ink hover:bg-ink-primary text-on-primary rounded-pill text-xs font-semibold uppercase tracking-[0.96px] transition shadow-soft"
          >
            + Create New Evaluation
          </a>
        </header>

        {/* Status Filter Pills */}
        <div className="flex gap-3 border-b border-hairline-soft pb-4">
          {["all", "pending", "active", "completed", "locked"].map((st) => (
            <button
              key={st}
              onClick={() => setFilter(st)}
              className={`px-4 py-1.5 rounded-pill text-xs uppercase tracking-[0.96px] transition ${
                filter === st
                  ? "bg-ink text-on-primary font-semibold"
                  : "bg-surface-strong text-muted hover:text-ink"
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
              <TableHeader className="bg-canvas-soft text-[11px] uppercase tracking-[0.96px] text-muted">
                <TableRow>
                  <TableHead className="p-6 font-semibold">Candidate</TableHead>
                  <TableHead className="p-6 font-semibold">Repository</TableHead>
                  <TableHead className="p-6 font-semibold">Status</TableHead>
                  <TableHead className="p-6 font-semibold">Final Score</TableHead>
                  <TableHead className="p-6 text-right font-semibold">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className="divide-y divide-hairline-soft">
                {filtered.map((ev) => (
                  <TableRow key={ev.id} className="hover:bg-canvas-soft/60 transition">
                    <TableCell className="p-6 font-serif font-normal text-lg text-ink">{ev.candidate}</TableCell>
                    <TableCell className="p-6 font-sans text-xs text-body font-mono">{ev.repo}</TableCell>
                    <TableCell className="p-6">
                      <StatusBadge status={ev.status} />
                    </TableCell>
                    <TableCell className="p-6 font-serif font-light text-2xl text-ink">
                      {ev.score !== null ? ev.score.toFixed(2) : "—"}
                    </TableCell>
                    <TableCell className="p-6 text-right">
                      <a
                        href={`/evaluations/${ev.id}`}
                        className="text-xs font-semibold uppercase tracking-[0.96px] text-ink hover:underline"
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
