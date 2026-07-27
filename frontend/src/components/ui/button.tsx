import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost"
  size?: "default" | "sm" | "lg"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap text-button transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink disabled:pointer-events-none disabled:opacity-50",
          {
            "bg-primary text-on-primary rounded-pill hover:bg-primary-active": variant === "default",
            "border border-hairline-strong bg-transparent text-ink rounded-pill hover:bg-canvas-soft": variant === "outline",
            "hover:bg-canvas-soft text-ink rounded-pill": variant === "ghost",
            "h-10 px-5 py-2.5": size === "default",
            "h-8 rounded-pill px-3 text-caption": size === "sm",
            "h-12 rounded-pill px-8 text-title-sm": size === "lg",
          },
          className
        )}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
