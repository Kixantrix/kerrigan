import { render, screen } from "@testing-library/react";
import App from "./App";

describe("App scaffold", () => {
  it("renders the placeholder route shell", () => {
    render(<App />);
    expect(screen.getByText("Portfolio route placeholder")).toBeVisible();
    expect(
      screen.getByText(
        "Scaffold ready (Tauri 2 + Vite + React + TypeScript + Tailwind 4).",
      ),
    ).toBeVisible();
  });
});
