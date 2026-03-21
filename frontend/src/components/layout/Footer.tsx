import { Leaf, Github, Linkedin, Mail } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border py-8 mt-auto">
      <div className="container mx-auto px-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Brand */}
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-600 text-white">
              <Leaf className="h-4 w-4" />
            </div>
            <div>
              <p className="font-bold text-foreground">Canopy</p>
              <p className="text-xs text-muted-foreground font-medium">Climate Risk Intelligence</p>
            </div>
          </div>

          {/* Tech Stack */}
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2.5 py-1 rounded-md bg-gray-50 border border-border text-muted-foreground font-medium">FastAPI</span>
            <span className="px-2.5 py-1 rounded-md bg-gray-50 border border-border text-muted-foreground font-medium">React</span>
            <span className="px-2.5 py-1 rounded-md bg-gray-50 border border-border text-muted-foreground font-medium">TanStack</span>
            <span className="px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">Claude AI</span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/griffinmacnaughtan"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg text-gray-400 hover:text-foreground hover:bg-gray-50 transition-colors"
              aria-label="GitHub"
            >
              <Github className="h-4 w-4" />
            </a>
            <a
              href="https://www.linkedin.com/in/griffin-macnaughtan"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg text-gray-400 hover:text-foreground hover:bg-gray-50 transition-colors"
              aria-label="LinkedIn"
            >
              <Linkedin className="h-4 w-4" />
            </a>
            <a
              href="mailto:gmacnaughtan@rogers.com"
              className="p-2 rounded-lg text-gray-400 hover:text-foreground hover:bg-gray-50 transition-colors"
              aria-label="Contact"
            >
              <Mail className="h-4 w-4" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
