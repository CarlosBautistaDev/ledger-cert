import * as React from "react";
import { cn } from "@/lib/utils";

/** Small status badge. */
export function Badge({
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>): React.ReactElement {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground",
        className,
      )}
      {...props}
    />
  );
}
