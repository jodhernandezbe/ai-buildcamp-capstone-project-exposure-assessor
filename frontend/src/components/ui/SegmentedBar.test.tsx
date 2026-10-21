import { render, screen } from "@testing-library/react";

import { SegmentedBar } from "./SegmentedBar";

const segments = [
  { label: "0-4", value: 10 },
  { label: "65+", value: 30 },
];

describe("SegmentedBar", () => {
  it("describes every band for assistive technology", () => {
    render(<SegmentedBar segments={segments} format={(v) => `${v}%`} />);
    expect(screen.getByRole("img", { name: "0-4: 10%, 65+: 30%" })).toBeInTheDocument();
  });

  it("sizes each band by its share of the total", () => {
    const { container } = render(<SegmentedBar segments={segments} format={(v) => `${v}%`} />);
    const widths = [...container.querySelectorAll<HTMLElement>('[role="img"] > div')].map((e) => e.style.width);
    expect(widths).toEqual(["25%", "75%"]);
  });

  it("draws nothing wide when there is no data", () => {
    const { container } = render(<SegmentedBar segments={[{ label: "x", value: 0 }]} format={String} />);
    expect(container.querySelector<HTMLElement>('[role="img"] > div')?.style.width).toBe("0%");
  });
});
