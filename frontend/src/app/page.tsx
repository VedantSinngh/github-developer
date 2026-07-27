import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="min-h-screen bg-canvas text-ink flex flex-col items-center justify-center p-6 relative overflow-hidden font-sans">
      {/* Background Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full gradient-orb-peach pointer-events-none opacity-50"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full gradient-orb-sky pointer-events-none opacity-50"></div>

      <div className="w-full max-w-2xl bg-surface-card border border-hairline rounded-xxl p-12 shadow-soft relative z-10 text-center space-y-8">
        <div className="space-y-4">
          <span className="text-[12px] uppercase tracking-[0.96px] font-semibold text-muted">
            Candidate Evaluation Platform
          </span>
          <h1 className="text-5xl font-serif font-light text-ink tracking-tight">
            Engineering Intelligence
          </h1>
          <p className="text-sm text-body max-w-md mx-auto leading-relaxed">
            Automated, unbiased, and comprehensive evaluation of software engineering candidates based on their real-world contributions.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link href="/login" className="w-full sm:w-auto">
            <Button className="w-full sm:w-auto rounded-pill shadow-soft px-8 py-6 text-sm">
              Sign In
            </Button>
          </Link>
          <Link href="/register" className="w-full sm:w-auto">
            <Button variant="outline" className="w-full sm:w-auto rounded-pill px-8 py-6 text-sm border-hairline hover:bg-canvas-soft">
              Register Organization
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
