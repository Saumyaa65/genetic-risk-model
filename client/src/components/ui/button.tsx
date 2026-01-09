import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
	variant?: "default" | "outline" | "ghost" | "secondary";
	size?: "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
	({ className, variant = "default", size, ...props }, ref) => {
		const base = "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none disabled:opacity-50 disabled:pointer-events-none"
		const variantClass =
			variant === "outline"
				? "border border-slate-200 bg-white text-slate-700"
				: variant === "ghost"
				? "bg-transparent text-slate-700"
				: variant === "secondary"
				? "bg-white text-slate-700"
				: "bg-teal-600 text-white"

		const sizeClass = size === "sm" ? "px-2 py-1" : size === "lg" ? "px-4 py-2" : size === "icon" ? "p-2" : "px-3 py-2"

		return (
			<button
				className={cn(base, variantClass, sizeClass, className)}
				ref={ref}
				{...props}
			/>
		)
	}
)
Button.displayName = "Button"

export { Button }
