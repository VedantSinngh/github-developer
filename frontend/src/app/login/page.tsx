"use client";

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
      const res = await fetch("http://localhost:8000/auth/login", {
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
    } catch (err: any) {
      setError(err.message);
    }
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

        <Form onSubmit={handleSubmit} className="space-y-5">
          {error && <div className="text-red-500 text-sm font-medium text-center">{error}</div>}
          <FormItem>
            <FormLabel className="text-[12px] uppercase tracking-[0.96px] text-muted mb-1.5">Email Address</FormLabel>
            <FormControl>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </FormControl>
          </FormItem>

          <Button type="submit" className="w-full rounded-pill shadow-soft">
            Sign In
          </Button>
        </Form>

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
