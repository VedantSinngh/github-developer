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
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/auth/register`, {
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
    <div className="py-section bg-canvas flex items-center justify-center relative overflow-hidden font-sans">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full gradient-orb-peach pointer-events-none opacity-40 mix-blend-multiply blur-3xl z-0"></div>

      <div className="w-full max-w-md bg-surface-card border border-hairline rounded-xl p-10 shadow-soft relative z-10 space-y-8">
        <div className="text-center space-y-4">
          <span className="text-caption-uppercase text-muted">
            ElevenLabs Editorial Platform
          </span>
          <h2 className="text-display-lg font-serif font-light text-ink tracking-tight">
            Register Org
          </h2>
          <p className="text-body-sm text-body">Create a new recruiter account</p>
        </div>

        {success ? (
          <div className="text-semantic-success text-center text-body-strong">
            Registration successful! Redirecting to login...
          </div>
        ) : (
          <Form onSubmit={handleSubmit} className="space-y-6">
            {error && <div className="text-semantic-error text-body-sm font-medium text-center">{error}</div>}
            
            <FormItem>
              <FormLabel className="text-caption-uppercase text-muted mb-2 block">Organization Name</FormLabel>
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
              Register
            </Button>
          </Form>
        )}

        <p className="text-body-sm text-center text-muted">
          Already have an account?{" "}
          <a href="/login" className="text-ink font-medium hover:underline transition-colors">
            Sign In
          </a>
        </p>
      </div>
    </div>
  );
}
