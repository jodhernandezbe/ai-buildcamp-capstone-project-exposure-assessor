import { Separator } from "react-resizable-panels";

type Axis = "column" | "row";

// The line is the 1px hairline; on hover, focus and drag a 3px accent line is drawn over it.
const SHARED =
  "relative shrink-0 bg-hairline outline-none after:absolute after:bg-transparent after:transition-colors after:content-[''] " +
  "data-[separator=hover]:after:bg-accent data-[separator=focus]:after:bg-accent data-[separator=active]:after:bg-accent";

const BY_AXIS: Record<Axis, string> = {
  column: "w-px after:inset-y-0 after:-left-px after:w-[3px]",
  row: "h-px after:inset-x-0 after:-top-px after:h-[3px]",
};

/**
 * A draggable divider. `column` divides side-by-side panels (a vertical line, col-resize);
 * `row` divides stacked panels. Keyboard arrows resize it when focused.
 */
export function PanelSplitter({ axis, label }: { axis: Axis; label: string }) {
  return <Separator aria-label={label} className={`${SHARED} ${BY_AXIS[axis]}`} />;
}
