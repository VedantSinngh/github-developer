import Link from "next/link";
import { Button } from "@/components/ui/button";

export function TopNav() {
  return (
    <nav className="h-[64px] bg-canvas text-ink border-b border-hairline flex items-center justify-between px-6 md:px-12 relative z-50">
      <div className="flex items-center gap-10">
        <Link href="/" className="font-serif font-light text-3xl tracking-tight text-ink">
          ElevenLabs
        </Link>
        <div className="hidden md:flex items-center gap-8">
          <Link href="#" className="text-nav-link text-body hover:text-ink transition-colors">Creative</Link>
          <Link href="#" className="text-nav-link text-body hover:text-ink transition-colors">Agents</Link>
          <Link href="#" className="text-nav-link text-body hover:text-ink transition-colors">Video</Link>
          <Link href="#" className="text-nav-link text-body hover:text-ink transition-colors">Pricing</Link>
          <Link href="#" className="text-nav-link text-body hover:text-ink transition-colors">Enterprise</Link>
          <Link href="#" className="text-nav-link text-body hover:text-ink transition-colors">Docs</Link>
        </div>
      </div>
      <div className="flex items-center gap-6">
        <Link href="/login" className="hidden md:block text-nav-link text-body hover:text-ink transition-colors">
          Sign In
        </Link>
        <Link href="/dashboard">
          <Button className="rounded-pill shadow-soft px-5 py-2">
            Try free
          </Button>
        </Link>
      </div>
    </nav>
  );
}
