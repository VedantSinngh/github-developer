"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormItem, FormLabel, FormControl } from "@/components/ui/form";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Login failed");
      }
      
      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      window.location.href = "/dashboard";
    } catch (err: unknown) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="py-section bg-canvas flex items-center justify-center relative overflow-hidden font-sans">
      {/* Background Mint Atmospheric Orb */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full gradient-orb-mint pointer-events-none opacity-40 mix-blend-multiply blur-3xl z-0"></div>

      <div className="w-full max-w-md bg-surface-card border border-hairline rounded-xl p-10 shadow-soft relative z-10 space-y-8">
        <div className="text-center space-y-4">
          <span className="text-caption-uppercase text-muted">
            ElevenLabs Editorial Platform
          </span>
          <h2 className="text-display-lg font-serif font-light text-ink tracking-tight">
            Recruiter Sign In
          </h2>
          <p className="text-body-sm text-body">Access candidate evaluation score cards</p>
        </div>

        <Form onSubmit={handleSubmit} className="space-y-6">
          {error && <div className="text-semantic-error text-body-sm font-medium text-center">{error}</div>}
          <FormItem>
            <FormLabel className="text-caption-uppercase text-muted mb-2 block">Email Address</FormLabel>
            <FormControl>
              <Input
                type="email"
                value={email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                placeholder="recruiter@company.com"
                required
              />
            </FormControl>
          </FormItem>

          <FormItem>
            <FormLabel className="text-caption-uppercase text-muted mb-2 block">Password</FormLabel>
            <FormControl>
              <Input
                type="password"
                value={password}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                required
              />
            </FormControl>
          </FormItem>

          <Button type="submit" className="w-full">
            Sign In
          </Button>
        </Form>

        <p className="text-body-sm text-center text-muted">
          Need a recruiter account?{" "}
          <a href="/register" className="text-ink font-medium hover:underline transition-colors">
            Register Organization
          </a>
        </p>
      </div>
    </div>
  );
}
