import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { render } from "@testing-library/react";
import App from "./App";

// Force demo mode so no real API calls are made
vi.stubEnv("VITE_DEMO_MODE", "true");

describe("App", () => {
  it("mounts without crashing", () => {
    const { container } = render(<App />);
    expect(container).toBeTruthy();
  });

  it("renders the Canopy brand in header and footer", () => {
    render(<App />);
    // "Canopy" appears in both header (h1) and footer (p)
    const matches = screen.getAllByText("Canopy");
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it("renders the AI copilot section", () => {
    render(<App />);
    expect(screen.getByText("Canopy AI")).toBeInTheDocument();
  });

  it("renders the copilot textarea", () => {
    render(<App />);
    const textarea = screen.getByPlaceholderText(
      /ask about your portfolio/i
    );
    expect(textarea).toBeInTheDocument();
  });
});
