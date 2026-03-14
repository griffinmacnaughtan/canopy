import { Leaf, Github, Linkedin, Mail } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-emerald-200/50 py-10 mt-auto bg-gradient-to-b from-white to-emerald-50/50">
      <div className="container mx-auto px-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500 to-forest-600 shadow-md shadow-emerald-500/20">
              <Leaf className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="font-bold text-foreground bg-gradient-to-r from-emerald-600 to-forest-600 bg-clip-text text-transparent">Canopy</p>
              <p className="text-xs text-emerald-600/70 font-medium">Climate Risk Intelligence</p>
            </div>
          </div>

          {/* Tech Stack */}
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2.5 py-1.5 rounded-lg bg-white border border-emerald-200/60 text-foreground font-medium shadow-sm">FastAPI</span>
            <span className="px-2.5 py-1.5 rounded-lg bg-white border border-emerald-200/60 text-foreground font-medium shadow-sm">React</span>
            <span className="px-2.5 py-1.5 rounded-lg bg-white border border-emerald-200/60 text-foreground font-medium shadow-sm">TanStack</span>
            <span className="px-2.5 py-1.5 rounded-lg bg-emerald-100 text-emerald-700 border border-emerald-200 font-semibold shadow-sm">Claude AI</span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-4">
            <a
              href="#"
              className="p-2 rounded-lg text-emerald-600/70 hover:text-emerald-600 hover:bg-emerald-100 transition-all"
              aria-label="GitHub"
            >
              <Github className="h-5 w-5" />
            </a>
            <a
              href="#"
              className="p-2 rounded-lg text-emerald-600/70 hover:text-emerald-600 hover:bg-emerald-100 transition-all"
              aria-label="LinkedIn"
            >
              <Linkedin className="h-5 w-5" />
            </a>
            <a
              href="#"
              className="p-2 rounded-lg text-emerald-600/70 hover:text-emerald-600 hover:bg-emerald-100 transition-all"
              aria-label="Contact"
            >
              <Mail className="h-5 w-5" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
