import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="bg-canvas text-ink relative overflow-hidden font-sans">
      {/* Hero Band */}
      <section className="relative pt-section pb-section px-6 md:px-12 flex flex-col items-center justify-center text-center min-h-[80vh]">
        
        {/* Atmospheric Gradient Orbs */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full gradient-orb-lavender pointer-events-none opacity-40 mix-blend-multiply blur-3xl z-0"></div>
        <div className="absolute top-1/4 right-1/4 w-[600px] h-[600px] rounded-full gradient-orb-peach pointer-events-none opacity-40 mix-blend-multiply blur-3xl z-0"></div>

        <div className="relative z-10 max-w-4xl space-y-8">
          <h1 className="text-display-mega text-ink font-serif font-light">
            Engineering Intelligence
          </h1>
          <p className="text-body-md text-body max-w-2xl mx-auto leading-relaxed">
            Automated, unbiased, and comprehensive evaluation of software engineering candidates based on their real-world contributions.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-8">
            <Link href="/register" className="w-full sm:w-auto">
              <Button className="w-full sm:w-auto h-12 rounded-pill shadow-soft px-8">
                Start Evaluating
              </Button>
            </Link>
            <Link href="/login" className="w-full sm:w-auto">
              <Button variant="outline" className="w-full sm:w-auto h-12 rounded-pill px-8 hover:bg-canvas-soft">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </section>
      
      {/* Additional sections can follow with py-section (96px) padding */}
      <section className="py-section px-6 md:px-12 bg-canvas-soft relative z-10 border-t border-hairline">
        <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16 space-y-4">
                <h2 className="text-display-lg text-ink font-serif font-light">
                    The New Standard for Hiring
                </h2>
                <p className="text-body-md text-body max-w-xl mx-auto">
                    Evaluate candidates based on their actual ability to build, debug, and ship software.
                </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Feature Cards */}
                <div className="bg-surface-card rounded-xl p-6 border border-hairline shadow-soft space-y-4">
                    <div className="w-12 h-12 rounded-full bg-surface-strong flex items-center justify-center mb-6">
                        <span className="text-xl">📊</span>
                    </div>
                    <h3 className="text-title-md text-ink">Objective Scoring</h3>
                    <p className="text-body-sm text-body">Data-driven insights into code quality, architecture, and problem-solving ability.</p>
                </div>
                <div className="bg-surface-card rounded-xl p-6 border border-hairline shadow-soft space-y-4">
                    <div className="w-12 h-12 rounded-full bg-surface-strong flex items-center justify-center mb-6">
                        <span className="text-xl">⚡</span>
                    </div>
                    <h3 className="text-title-md text-ink">Automated Reviews</h3>
                    <p className="text-body-sm text-body">Save hundreds of engineering hours with instant, comprehensive code reviews.</p>
                </div>
                <div className="bg-surface-card rounded-xl p-6 border border-hairline shadow-soft space-y-4">
                    <div className="w-12 h-12 rounded-full bg-surface-strong flex items-center justify-center mb-6">
                        <span className="text-xl">🤝</span>
                    </div>
                    <h3 className="text-title-md text-ink">Fair Evaluation</h3>
                    <p className="text-body-sm text-body">Eliminate bias by focusing purely on the code and architectural decisions.</p>
                </div>
            </div>
        </div>
      </section>
    </div>
  );
}
