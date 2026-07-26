"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormItem, FormLabel, FormControl } from "@/components/ui/form";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [orgName, setOrgName] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    try {
      const res = await fetch("http://localhost:8000/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, org_name: orgName }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Registration failed");
      }

      setSuccess(true);
      setTimeout(() => {
        window.location.href = "/login";
      }, 2000);
    } catch (err: unknown) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center p-6 relative overflow-hidden font-sans">
      <div className="absolute top-1/4 right-1/2 translate-x-1/2 w-96 h-96 rounded-full gradient-orb-peach pointer-events-none opacity-80"></div>

      <div className="w-full max-w-md bg-surface-card border border-hairline rounded-xxl p-10 shadow-soft relative z-10 space-y-8">
        <div className="text-center space-y-2">
          <span className="text-[12px] uppercase tracking-[0.96px] font-semibold text-muted">
            ElevenLabs Editorial Platform
          </span>
          <h2 className="text-4xl font-serif font-light text-ink tracking-tight">
            Register Org
          </h2>
          <p className="text-xs text-body">Create a new recruiter account</p>
        </div>

        {success ? (
          <div className="text-green-600 text-center font-medium">
            Registration successful! Redirecting to login...
          </div>
        ) : (
          <Form onSubmit={handleSubmit} className="space-y-5">
            {error && <div className="text-red-500 text-sm font-medium text-center">{error}</div>}
            
            <FormItem>
              <FormLabel className="text-[12px] uppercase tracking-[0.96px] text-muted mb-1.5">Organization Name</FormLabel>
              <FormControl>
                <Input
                  type="text"
                  value={orgName}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOrgName(e.target.value)}
                  placeholder="Acme Corp"
                  required
                />
              </FormControl>
            </FormItem>

            <FormItem>
              <FormLabel className="text-[12px] uppercase tracking-[0.96px] text-muted mb-1.5">Email Address</FormLabel>
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
              <FormLabel className="text-[12px] uppercase tracking-[0.96px] text-muted mb-1.5">Password</FormLabel>
              <FormControl>
                <Input
                  type="password"
                  value={password}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                  required
                />
              </FormControl>
            </FormItem>

            <Button type="submit" className="w-full rounded-pill shadow-soft">
              Register
            </Button>
          </Form>
        )}

        <p className="text-xs text-center text-muted">
          Already have an account?{" "}
          <a href="/login" className="text-ink font-semibold hover:underline">
            Sign In
          </a>
        </p>
      </div>
    </div>
  );
}
