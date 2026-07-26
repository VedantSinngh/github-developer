"use client";

import React, { useState } from "react";

export default function NewEvaluationPage() {
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [githubUsername, setGithubUsername] = useState("");
  const [repoOwner, setRepoOwner] = useState("");
  const [repoName, setRepoName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    window.location.href = "/dashboard";
  };

  return (
    <div className="min-h-screen bg-canvas text-ink p-12 font-sans relative overflow-hidden">
      {/* Background Lavender Orb */}
      <div className="absolute top-20 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full gradient-orb-lavender pointer-events-none opacity-60"></div>

      <div className="max-w-2xl mx-auto bg-surface-card border border-hairline rounded-xxl p-10 shadow-soft relative z-10 space-y-8">
        <div>
          <span className="text-[12px] uppercase tracking-[0.96px] font-semibold text-muted">
            Evaluation Setup
          </span>
          <h1 className="text-4xl font-serif font-light text-ink tracking-tight mt-1">
            New Candidate Window
          </h1>
          <p className="text-xs text-body mt-1">
            Configure time-boxed window and repository for window-bounded sync.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[12px] uppercase tracking-[0.96px] font-semibold text-muted mb-1.5">
                Candidate Name
              </label>
              <input
                type="text"
                value={candidateName}
                onChange={(e) => setCandidateName(e.target.value)}
                className="w-full bg-surface-card border border-hairline-strong rounded-lg px-4 py-2.5 text-sm text-ink focus:outline-none focus:border-ink transition"
                required
              />
            </div>
            <div>
              <label className="block text-[12px] uppercase tracking-[0.96px] font-semibold text-muted mb-1.5">
                Candidate Email
              </label>
              <input
                type="email"
                value={candidateEmail}
                onChange={(e) => setCandidateEmail(e.target.value)}
                className="w-full bg-surface-card border border-hairline-strong rounded-lg px-4 py-2.5 text-sm text-ink focus:outline-none focus:border-ink transition"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-[12px] uppercase tracking-[0.96px] font-semibold text-muted mb-1.5">
                GitHub Username
              </label>
              <input
                type="text"
                value={githubUsername}
                onChange={(e) => setGithubUsername(e.target.value)}
                className="w-full bg-surface-card border border-hairline-strong rounded-lg px-4 py-2.5 text-sm text-ink focus:outline-none focus:border-ink transition"
                required
              />
            </div>
            <div>
              <label className="block text-[12px] uppercase tracking-[0.96px] font-semibold text-muted mb-1.5">
                Repo Owner
              </label>
              <input
                type="text"
                value={repoOwner}
                onChange={(e) => setRepoOwner(e.target.value)}
                className="w-full bg-surface-card border border-hairline-strong rounded-lg px-4 py-2.5 text-sm text-ink focus:outline-none focus:border-ink transition"
                required
              />
            </div>
            <div>
              <label className="block text-[12px] uppercase tracking-[0.96px] font-semibold text-muted mb-1.5">
                Repo Name
              </label>
              <input
                type="text"
                value={repoName}
                onChange={(e) => setRepoName(e.target.value)}
                className="w-full bg-surface-card border border-hairline-strong rounded-lg px-4 py-2.5 text-sm text-ink focus:outline-none focus:border-ink transition"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[12px] uppercase tracking-[0.96px] font-semibold text-muted mb-1.5">
                Start Window
              </label>
              <input
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-surface-card border border-hairline-strong rounded-lg px-4 py-2.5 text-sm text-ink focus:outline-none focus:border-ink transition"
                required
              />
            </div>
            <div>
              <label className="block text-[12px] uppercase tracking-[0.96px] font-semibold text-muted mb-1.5">
                End Window
              </label>
              <input
                type="datetime-local"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full bg-surface-card border border-hairline-strong rounded-lg px-4 py-2.5 text-sm text-ink focus:outline-none focus:border-ink transition"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-ink hover:bg-ink-primary text-on-primary font-medium py-3 rounded-pill text-sm transition shadow-soft mt-2"
          >
            Create Evaluation Window
          </button>
        </form>
      </div>
    </div>
  );
}
