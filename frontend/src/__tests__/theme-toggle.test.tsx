import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeProvider } from "@/contexts/ThemeContext";
import ThemeToggle from "@/components/ThemeToggle";

describe("ThemeProvider + ThemeToggle", () => {
  it("toggles theme", () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>,
    );
    const btn = screen.getByRole("button");
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    // Should cycle theme (light/dark/system)
    fireEvent.click(btn);
    fireEvent.click(btn);
  });
});
