import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/test-utils";
import { Header } from "./Header";

// Force demo mode for deterministic mock data
vi.stubEnv("VITE_DEMO_MODE", "true");

describe("Header", () => {
  it("renders the brand name", () => {
    renderWithProviders(<Header />);
    expect(screen.getByText("Canopy")).toBeInTheDocument();
  });

  it("renders the tagline", () => {
    renderWithProviders(<Header />);
    expect(screen.getByText("Climate Risk Intelligence")).toBeInTheDocument();
  });

  it("renders action buttons", () => {
    renderWithProviders(<Header />);
    expect(screen.getByText("Export")).toBeInTheDocument();
    expect(screen.getByText("Import")).toBeInTheDocument();
    expect(screen.getByText("New Portfolio")).toBeInTheDocument();
  });

  it("brand is wrapped in a link to home", () => {
    renderWithProviders(<Header />);
    const brandLink = screen.getByText("Canopy").closest("a");
    expect(brandLink).toHaveAttribute("href");
  });

  it("shows Demo connection badge in demo mode", () => {
    renderWithProviders(<Header />);
    expect(screen.getByText("Demo")).toBeInTheDocument();
  });
});
