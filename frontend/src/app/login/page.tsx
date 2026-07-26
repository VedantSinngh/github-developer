"use client";

import React, { useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem("token", "synthetic_jwt_token");
    window.location.href = "/dashboard";
  };

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center p-6 relative overflow-hidden font-sans">
      {/* Background Mint Atmospheric Orb */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full gradient-orb-mint pointer-events-none opacity-80"></div>

      <div className="w-full max-w-md bg-surface-card border border-hairline rounded-xxl p-10 shadow-soft relative z-10 space-y-8">
        <div className="text-center space-y-2">
          <span className="text-[12px] uppercase tracking-[0.96px] font-semibold text-muted">
            ElevenLabs Editorial Platform
          </span>
          <h2 className="text-4xl font-serif font-light text-ink tracking-tight">
            Recruiter Sign In
          </h2>
          <p className="text-xs text-body">Access candidate evaluation score cards</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-[12px] uppercase tracking-[0.96px] font-semibold text-muted mb-1.5">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-surface-card border border-hairline-strong rounded-lg px-4 py-2.5 text-sm text-ink focus:outline-none focus:border-ink transition"
              placeholder="recruiter@company.com"
              required
            />
          </div>

          <div>
            <label className="block text-[12px] uppercase tracking-[0.96px] font-semibold text-muted mb-1.5">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-surface-card border border-hairline-strong rounded-lg px-4 py-2.5 text-sm text-ink focus:outline-none focus:border-ink transition"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-ink hover:bg-ink-primary text-on-primary font-medium py-3 rounded-pill text-sm transition shadow-soft"
          >
            Sign In
          </button>
        </form>

        <p className="text-xs text-center text-muted">
          Need a recruiter account?{" "}
          <a href="/register" className="text-ink font-semibold hover:underline">
            Register Organization
          </a>
        </p>
      </div>
    </div>
  );
}
