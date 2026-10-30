import { render, screen, within } from "@testing-library/react";

import { BrandLogo, BrandMark } from "./BrandLogo";

describe("BrandMark", () => {
  it("is decorative and draws the simplified mark at small sizes", () => {
    const { container } = render(<BrandMark size={32} />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("aria-hidden", "true");
    expect(svg).toHaveAttribute("viewBox", "0 0 64 64");
  });

  it("gives every detailed instance its own gradient ids", () => {
    const { container } = render(
      <>
        <BrandMark size={48} />
        <BrandMark size={48} />
      </>,
    );
    const ids = [...container.querySelectorAll("linearGradient")].map((node) => node.id);
    expect(ids).toHaveLength(8);
    expect(new Set(ids).size).toBe(8);
    for (const id of ids) expect(id).toMatch(/^[a-zA-Z0-9_-]+$/);
  });
});

describe("BrandLogo", () => {
  it("shows the wordmark with its micro-label", () => {
    render(<BrandLogo label="Exposure & Risk Studio" />);
    expect(screen.getByText("EcoFate")).toBeInTheDocument();
    expect(screen.getByText("Exposure & Risk Studio")).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Compartments" })).toBeNull();
  });

  it("marks air as available and water and soil as planned", () => {
    render(<BrandLogo compartments />);
    const items = within(screen.getByRole("list", { name: "Compartments" })).getAllByRole("listitem");
    expect(items.map((item) => item.textContent)).toEqual(["Air", "Water (planned)", "Soil (planned)"]);
    expect(items[1]).toHaveAttribute("title", expect.stringContaining("planned"));
  });
});
