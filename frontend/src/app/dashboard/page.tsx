"use client";

import React, { useState, useEffect } from "react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

type Cohort = {
  id: number;
  name: string;
  role_level: string;
  tech_stack: string;
  start_date: string;
  end_date: string;
  is_rubric_locked: boolean;
};

export default function DashboardPage() {
  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${API_URL}/cohorts`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch cohorts");
        return res.json();
      })
      .then((data) => {
        setCohorts(data);
      })
      .catch((err) => console.error("Error fetching cohorts:", err))
      .finally(() => setLoading(false));
  }, []);

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
              Cohorts Index
            </h1>
          </div>
          <a
            href="/cohorts/new"
            className="inline-flex h-10 items-center justify-center rounded-pill bg-primary px-5 text-button text-on-primary hover:bg-primary-active transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink"
          >
            + Create New Cohort
          </a>
        </header>

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
                  <TableHead className="p-6 font-medium">Cohort Name</TableHead>
                  <TableHead className="p-6 font-medium">Role & Stack</TableHead>
                  <TableHead className="p-6 font-medium">Status</TableHead>
                  <TableHead className="p-6 text-right font-medium">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className="divide-y divide-hairline-soft">
                {cohorts.map((cohort: Cohort) => (
                  <TableRow key={cohort.id} className="hover:bg-canvas-soft transition-colors">
                    <TableCell className="p-6 font-serif font-light text-2xl text-ink tracking-tight">{cohort.name}</TableCell>
                    <TableCell className="p-6 text-body-sm text-body font-mono">{cohort.role_level} - {cohort.tech_stack}</TableCell>
                    <TableCell className="p-6 font-mono text-sm">
                      {cohort.is_rubric_locked ? (
                        <span className="text-green-600 bg-green-100 px-2 py-1 rounded">Started</span>
                      ) : (
                        <span className="text-yellow-600 bg-yellow-100 px-2 py-1 rounded">Pending</span>
                      )}
                    </TableCell>
                    <TableCell className="p-6 text-right">
                      <a
                        href={`/cohorts/${cohort.id}`}
                        className="text-caption-uppercase text-ink hover:underline font-bold"
                      >
                        View Dashboard →
                      </a>
                    </TableCell>
                  </TableRow>
                ))}
                {cohorts.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="p-6 text-center text-muted">
                      No cohorts found. Create one to get started.
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
