import { Maximize2, Minimize2 } from "lucide-react";
import { useMemo } from "react";

import type { Thresholds } from "../../types/api";
import type { Facility } from "../../types/workspace";
import { isAssessed } from "./assessment";
import { RiskGroupChart } from "./RiskGroupChart";
import { groupFacilities, type GroupBy, type RankBy, topGroups, TOP_N } from "./riskGroups";

const COPY: Record<GroupBy, { title: string; ungrouped: string; overlap: boolean }> = {
  subsector: { title: "Risk by industry (NAICS subsector)", ungrouped: "industry not reported", overlap: false },
  condition: { title: "Risk by condition of use", ungrouped: "no condition of use reported", overlap: true },
  stage: { title: "Risk by life cycle stage", ungrouped: "no life cycle stage reported", overlap: true },
};

const RANKINGS: { key: RankBy; label: string }[] = [
  { key: "hq", label: "Hazard quotient" },
  { key: "risk", label: "Cancer risk" },
];

const SHORT_LABEL_CHARS = 16;
const LONG_LABEL_CHARS = 30;

interface Props {
  by: GroupBy;
  facilities: Facility[];
  rankBy: RankBy;
  onRankBy: (rankBy: RankBy) => void;
  expanded: boolean;
  /** Another section is expanded: this one stays mounted but is not shown. */
  hidden: boolean;
  onToggleExpand: () => void;
  thresholds: Thresholds | undefined;
  digits: number;
}

function RankSwitch({ rankBy, onRankBy }: { rankBy: RankBy; onRankBy: (rankBy: RankBy) => void }) {
  return (
    <div role="group" aria-label="Rank groups by" className="inline-flex rounded-full bg-fg2/10 p-0.5 text-[11px]">
      {RANKINGS.map(({ key, label }) => (
        <button
          key={key}
          type="button"
          aria-pressed={rankBy === key}
          onClick={() => onRankBy(key)}
          className={`spring rounded-full px-2 py-0.5 ${rankBy === key ? "bg-solid font-medium text-fg shadow-sm" : "text-fg2 hover:text-fg"}`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function Notes({ by, ungrouped, hidden, rankBy }: { by: GroupBy; ungrouped: number; hidden: number; rankBy: RankBy }) {
  const copy = COPY[by];
  const lines = [
    `Highest worst-case value among assessed facilities in each group; top ${TOP_N} by ${rankBy === "hq" ? "hazard quotient" : "cancer risk"}.`,
    copy.overlap ? "A facility with several conditions of use appears in each, so bars can overlap." : null,
    hidden > 0 ? `${hidden} more ${hidden === 1 ? "group" : "groups"} not shown.` : null,
    ungrouped > 0 ? `${ungrouped} ${ungrouped === 1 ? "facility" : "facilities"}: ${copy.ungrouped}.` : null,
  ].filter((line): line is string => line !== null);
  return (
    <ul className="m-0 list-none p-0 text-[11px] text-fg2">
      {lines.map((line) => (
        <li key={line}>{line}</li>
      ))}
    </ul>
  );
}

/** One top-5 chart of the worst-case HQ and cancer risk by a grouping of the facilities. */
export function RiskGroupSection(props: Props) {
  const { by, facilities, rankBy, expanded, hidden, thresholds, digits } = props;
  const copy = COPY[by];
  const grouping = useMemo(() => groupFacilities(facilities, by), [facilities, by]);
  const { shown, hidden: cut } = useMemo(() => topGroups(grouping.groups, rankBy), [grouping, rankBy]);
  const anyAssessed = useMemo(() => facilities.some(isAssessed), [facilities]);
  const Icon = expanded ? Minimize2 : Maximize2;
  return (
    <section
      aria-label={copy.title}
      hidden={hidden}
      className={`glass flex min-w-0 flex-col gap-2 rounded-2xl p-3.5 ${hidden ? "hidden" : ""} ${expanded ? "col-span-full flex-1" : ""}`}
    >
      <header className="flex items-start justify-between gap-2">
        <h2 className="m-0 text-xs font-semibold uppercase tracking-wide text-fg2">{copy.title}</h2>
        <div className="flex items-center gap-1.5">
          <RankSwitch rankBy={rankBy} onRankBy={props.onRankBy} />
          <button
            type="button"
            aria-label={expanded ? "Restore section" : "Expand section"}
            aria-pressed={expanded}
            onClick={props.onToggleExpand}
            className="spring grid size-6 place-items-center rounded-full text-fg2 transition hover:bg-hairline hover:text-fg"
          >
            <Icon size={14} aria-hidden="true" />
          </button>
        </div>
      </header>
      {shown.length > 0 ? (
        <RiskGroupChart
          groups={shown}
          thresholds={thresholds}
          digits={digits}
          caption={copy.title}
          labelChars={expanded ? LONG_LABEL_CHARS : SHORT_LABEL_CHARS}
          heightClass={expanded ? "h-[62vh] min-h-72" : "h-56"}
          angled={!expanded}
        />
      ) : (
        <div className="grid h-56 place-items-center rounded-lg border border-dashed border-hairline px-3 text-center">
          <p className="m-0 text-sm text-fg2">
            {facilities.length === 0
              ? "Nothing to show yet. Run an assessment and this chart ranks its facilities."
              : anyAssessed
                ? `No group has a worst-case ${rankBy === "hq" ? "hazard quotient" : "cancer risk"} to rank.`
                : "Nothing assessed yet: no facility has a worst-case result."}
          </p>
        </div>
      )}
      <Notes by={by} ungrouped={grouping.ungrouped} hidden={cut} rankBy={rankBy} />
    </section>
  );
}
