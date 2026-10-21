import type { ComponentProps } from "react";

/** A translucent surface with a hairline border. */
export function GlassCard({ className = "", ...props }: ComponentProps<"div">) {
  return <div className={`glass rounded-2xl ${className}`} {...props} />;
}
