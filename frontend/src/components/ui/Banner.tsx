import { CircleAlert, CircleCheck } from "lucide-react";

/** An inline success or error message; errors interrupt assistive technology, success does not. */
export function Banner({ kind, children }: { kind: "success" | "error"; children: string }) {
  const Icon = kind === "success" ? CircleCheck : CircleAlert;
  return (
    <p
      role={kind === "error" ? "alert" : "status"}
      className={`flex items-start gap-2 rounded-xl border border-hairline px-3 py-2 text-sm ${
        kind === "success" ? "text-ok" : "text-bad"
      }`}
    >
      <Icon size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
      <span>{children}</span>
    </p>
  );
}
