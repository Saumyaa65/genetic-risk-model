import * as React from "react"
import { cn } from "@/lib/utils"

const Card = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
	<div className={cn("rounded-lg bg-white p-4 shadow-sm", className)} {...props} />
)

const CardHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
	<div className={cn("mb-4", className)} {...props} />
)

const CardTitle = ({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
	<h3 className={cn("text-lg font-semibold", className)} {...props} />
)

const CardDescription = ({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
	<p className={cn("text-sm text-slate-500", className)} {...props} />
)

const CardContent = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
	<div className={cn("p-2", className)} {...props} />
)

export { Card, CardHeader, CardTitle, CardDescription, CardContent }
