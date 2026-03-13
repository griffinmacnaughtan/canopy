import { ReactNode } from "react";
import { Header } from "./Header";
import { Footer } from "./Footer";
import { Toaster } from "sonner";

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-6 py-8">{children}</main>
      <Footer />
      <Toaster
        position="bottom-right"
        toastOptions={{
          className: "bg-card border border-border text-foreground",
        }}
      />
    </div>
  );
}
