import { render, screen } from "@testing-library/react";

import { StatusPill } from "./StatusPill";

describe("StatusPill", () => {
  it.each([
    ["below", "Below concern"],
    ["near", "Near concern"],
    ["above", "Above concern"],
    [null, "Not computed"],
  ] as const)("says %s in words", (status, label) => {
    render(<StatusPill status={status} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });
});

describe("StatusPill label", () => {
  it("replaces the default words but keeps the status", () => {
    render(<StatusPill status="above" label="Exceedance" />);
    expect(screen.getByText("Exceedance")).toHaveAttribute("data-status", "above");
  });
});
