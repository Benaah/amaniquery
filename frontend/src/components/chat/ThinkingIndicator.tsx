"use client"

import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Brain, ChevronDown, ChevronRight, Check, Clock, Search, Lightbulb } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface ThinkingStep {
  id: string
  title: string
  status: "pending" | "active" | "completed"
  duration?: number
  details?: string
}

interface ThinkingIndicatorProps {
  isActive: boolean
  steps?: ThinkingStep[]
  currentStep?: number
  className?: string
  onToggle?: (expanded: boolean) => void
  defaultExpanded?: boolean
}

const defaultThinkingSteps: ThinkingStep[] = [
  { id: "1", title: "Understanding your question", status: "pending" },
  { id: "2", title: "Searching relevant information", status: "pending" },
  { id: "3", title: "Analyzing sources", status: "pending" },
  { id: "4", title: "Formulating response", status: "pending" }
]

export function ThinkingIndicator({ 
  isActive, 
  steps = defaultThinkingSteps,
  currentStep = 0,
  className,
  onToggle,
  defaultExpanded = false
}: ThinkingIndicatorProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const [activeSteps, setActiveSteps] = useState(steps)

  useEffect(() => {
    if (isActive) {
      const timer = setInterval(() => {
        setActiveSteps(prev => {
          const newSteps = [...prev]
          const currentActiveIndex = newSteps.findIndex(step => step.status === "active")
          
          if (currentActiveIndex >= 0 && currentActiveIndex < newSteps.length - 1) {
            newSteps[currentActiveIndex].status = "completed"
            newSteps[currentActiveIndex + 1].status = "active"
          } else if (currentActiveIndex === -1 && newSteps.length > 0) {
            newSteps[0].status = "active"
          }
          
          return newSteps
        })
      }, 2000)

      return () => clearInterval(timer)
    }
  }, [isActive])

  useEffect(() => {
    if (!isActive) {
      setActiveSteps(steps.map(step => ({ ...step, status: "pending" })))
    }
  }, [isActive, steps])

  const handleToggle = () => {
    const newExpanded = !isExpanded
    setIsExpanded(newExpanded)
    onToggle?.(newExpanded)
  }

  const getStepIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <Check className="w-4 h-4 text-green-600" />
      case "active":
        return <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      default:
        return <div className="w-4 h-4 rounded-full border-2 border-muted-foreground/30" />
    }
  }

  if (!isActive) return null

  return (
    <Card className={cn("border-primary/20 bg-primary/5", className)}>
      <CardHeader 
        className="cursor-pointer hover:bg-primary/10 transition-colors py-3"
        onClick={handleToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="w-5 h-5 text-primary animate-pulse" />
            <CardTitle className="text-base font-medium">Thinking</CardTitle>
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            )}
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="w-3 h-3" />
            <span>Analyzing...</span>
          </div>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-0 pb-4">
          <div className="space-y-3">
            {activeSteps.map((step, index) => (
              <div 
                key={step.id}
                className={cn(
                  "flex items-center gap-3 p-2 rounded-lg transition-all",
                  step.status === "active" && "bg-primary/10",
                  step.status === "completed" && "opacity-75"
                )}
              >
                {getStepIcon(step.status)}
                <div className="flex-1">
                  <div className={cn(
                    "text-sm font-medium",
                    step.status === "active" ? "text-foreground" : "text-muted-foreground"
                  )}>
                    {step.title}
                  </div>
                  {step.details && step.status === "active" && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {step.details}
                    </div>
                  )}
                </div>
                {step.status === "active" && (
                  <Search className="w-4 h-4 text-primary animate-pulse" />
                )}
                {step.status === "completed" && step.duration && (
                  <span className="text-xs text-muted-foreground">
                    {step.duration}ms
                  </span>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  )
}

interface CompactThinkingIndicatorProps {
  isActive: boolean
  className?: string
}

export function CompactThinkingIndicator({ isActive, className }: CompactThinkingIndicatorProps) {
  if (!isActive) return null

  return (
    <div className={cn(
      "inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-sm",
      className
    )}>
      <Brain className="w-4 h-4 animate-pulse" />
      <span>Thinking...</span>
      <div className="flex gap-1">
        <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  )
}