import Link from "next/link";
import { Wrench, ShieldCheck, Truck, RefreshCcw } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 py-12 mt-auto">
      <div className="container mx-auto px-4">
        {/* Trust Badges */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 border-b border-slate-800 pb-12 mb-12">
          <div className="flex flex-col items-center text-center gap-2">
            <div className="bg-slate-800 p-3 rounded-full text-accent">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h4 className="font-semibold text-slate-100">Genuine Parts</h4>
            <p className="text-sm text-slate-400">100% authentic materials from trusted brands.</p>
          </div>
          <div className="flex flex-col items-center text-center gap-2">
            <div className="bg-slate-800 p-3 rounded-full text-accent">
              <Truck className="w-6 h-6" />
            </div>
            <h4 className="font-semibold text-slate-100">Fast Delivery</h4>
            <p className="text-sm text-slate-400">Next-day shipping on in-stock items.</p>
          </div>
          <div className="flex flex-col items-center text-center gap-2">
            <div className="bg-slate-800 p-3 rounded-full text-accent">
              <RefreshCcw className="w-6 h-6" />
            </div>
            <h4 className="font-semibold text-slate-100">Easy Returns</h4>
            <p className="text-sm text-slate-400">30-day return policy on unused items.</p>
          </div>
        </div>

        {/* Links */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8">
          <div className="flex flex-col gap-4">
            <Link href="/" className="flex items-center gap-2 text-white font-bold text-xl tracking-tight">
              <Wrench className="w-6 h-6 text-accent" />
              <span>Supreme Hardware</span>
            </Link>
            <p className="text-sm text-slate-400 max-w-xs">
              Your trusted supplier for industrial and residential plumbing materials.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-white mb-4">Shop</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/category/pvc-pipes" className="hover:text-accent transition-colors">PVC Pipes</Link></li>
              <li><Link href="/category/fittings" className="hover:text-accent transition-colors">Fittings</Link></li>
              <li><Link href="/category/valves" className="hover:text-accent transition-colors">Valves</Link></li>
              <li><Link href="/category/tools" className="hover:text-accent transition-colors">Tools</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-white mb-4">Support</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/faq" className="hover:text-accent transition-colors">FAQ</Link></li>
              <li><Link href="/shipping" className="hover:text-accent transition-colors">Shipping Policy</Link></li>
              <li><Link href="/returns" className="hover:text-accent transition-colors">Returns</Link></li>
              <li><Link href="/contact" className="hover:text-accent transition-colors">Contact Us</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-white mb-4">Contact</h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li>123 Industrial Park, Sector 4</li>
              <li>Cityville, ST 12345</li>
              <li>support@supremehardware.com</li>
              <li>+1 (555) 123-4567</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-800 mt-12 pt-8 text-sm text-center text-slate-500">
          &copy; {new Date().getFullYear()} Supreme Hardware Store. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
