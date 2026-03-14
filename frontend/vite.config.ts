import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  // For GitHub Pages deployment - set to repo name
  // e.g., base: '/canopy/' for https://username.github.io/canopy/
  base: mode === "production" ? "/canopy/" : "/",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    // Generate source maps for debugging
    sourcemap: mode !== "production",
    // Optimize chunk sizes
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          charts: ["recharts"],
          ui: ["framer-motion", "lucide-react"],
        },
      },
    },
  },
  define: {
    // Make env variables available
    "import.meta.env.VITE_DEMO_MODE": JSON.stringify(process.env.VITE_DEMO_MODE || "false"),
  },
}));
