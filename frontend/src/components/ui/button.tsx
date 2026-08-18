import * as React from "react";
import { cn } from "@/lib/utils";

type Variant = "default" | "outline" | "destructive";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const styles: Record<Variant, string> = {
  default: "bg-primary text-primary-foreground hover:opacity-90",
  outline: "border border-input bg-transparent hover:bg-secondary",
  destructive: "bg-destructive text-destructive-foreground hover:opacity-90",
};

/** Basic button primitive. */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition disabled:pointer-events-none disabled:opacity-50",
        styles[variant],
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";
