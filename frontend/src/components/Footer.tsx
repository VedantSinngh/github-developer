import Link from "next/link";

export function Footer() {
  return (
    <footer className="bg-canvas border-t border-hairline px-6 md:px-12 py-16 md:py-24 z-10 relative">
      <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-5 gap-10 md:gap-8">
        <div className="col-span-2 md:col-span-1 space-y-4">
          <Link href="/" className="font-serif font-light text-3xl text-ink tracking-tight">
            ElevenLabs
          </Link>
          <p className="text-body-sm text-muted">
            Engineering Intelligence Platform
          </p>
        </div>
        
        <div className="space-y-6">
          <h4 className="text-caption-uppercase text-ink">Products</h4>
          <ul className="space-y-4">
            <li><Link href="#" className="text-body-sm text-body hover:text-ink transition-colors">Creative</Link></li>
            <li><Link href="#" className="text-body-sm text-body hover:text-ink transition-colors">Agents</Link></li>
            <li><Link href="#" className="text-body-sm text-body hover:text-ink transition-colors">Video</Link></li>
          </ul>
        </div>

        <div className="space-y-6">
          <h4 className="text-caption-uppercase text-ink">Resources</h4>
          <ul className="space-y-4">
            <li><Link href="#" className="text-body-sm text-body hover:text-ink transition-colors">Docs</Link></li>
            <li><Link href="#" className="text-body-sm text-body hover:text-ink transition-colors">API Reference</Link></li>
            <li><Link href="#" className="text-body-sm text-body hover:text-ink transition-colors">Help Center</Link></li>
          </ul>
        </div>

        <div className="space-y-6">
          <h4 className="text-caption-uppercase text-ink">Company</h4>
          <ul className="space-y-4">
            <li><Link href="#" className="text-body-sm text-body hover:text-ink transition-colors">About</Link></li>
            <li><Link href="#" className="text-body-sm text-body hover:text-ink transition-colors">Careers</Link></li>
            <li><Link href="#" className="text-body-sm text-body hover:text-ink transition-colors">Blog</Link></li>
          </ul>
        </div>

        <div className="space-y-6">
          <h4 className="text-caption-uppercase text-ink">Legal</h4>
          <ul className="space-y-4">
            <li><Link href="#" className="text-body-sm text-body hover:text-ink transition-colors">Privacy Policy</Link></li>
            <li><Link href="#" className="text-body-sm text-body hover:text-ink transition-colors">Terms of Service</Link></li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
