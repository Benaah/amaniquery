"use client"

import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import { ChevronDown, ChevronRight, Check, Loader2, Sparkles } from "lucide-react"

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
  { id: "1", title: "Analyzing request", status: "pending" },
  { id: "2", title: "Searching knowledge base", status: "pending" },
  { id: "3", title: "Reviewing sources", status: "pending" },
  { id: "4", title: "Generating answer", status: "pending" }
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
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (isActive) {
      const startTime = Date.now()
      const timer = setInterval(() => {
        setElapsed(Math.floor((Date.now() - startTime) / 1000))
        
        setActiveSteps(prev => {
          const newSteps = [...prev]
          const currentActiveIndex = newSteps.findIndex(step => step.status === "active")
          
          if (currentActiveIndex >= 0 && currentActiveIndex < newSteps.length - 1) {
            // Simulate progression randomly
            if (Math.random() > 0.7) {
                newSteps[currentActiveIndex].status = "completed"
                newSteps[currentActiveIndex + 1].status = "active"
            }
          } else if (currentActiveIndex === -1 && newSteps.length > 0) {
            newSteps[0].status = "active"
          }
          
          return newSteps
        })
      }, 800)

      return () => clearInterval(timer)
    } else {
        setElapsed(0)
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

  if (!isActive) return null

  return (
    <div className={cn("text-sm", className)}>
      <button 
        className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded-md hover:bg-muted/50"
        onClick={handleToggle}
      >
        <Sparkles className="w-4 h-4 text-purple-500 animate-pulse" />
        <span className="font-medium italic">Thinking process...</span>
        <span className="text-xs opacity-70 tabular-nums">({elapsed}s)</span>
        {isExpanded ? (
          <ChevronDown className="w-3.5 h-3.5" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-2 ml-2 pl-4 border-l-2 border-muted space-y-2 animate-in slide-in-from-top-2 duration-200">
          {activeSteps.map((step) => (
            <div 
              key={step.id}
              className={cn(
                "flex items-center gap-2 text-xs transition-colors",
                step.status === "active" ? "text-primary font-medium" : "text-muted-foreground",
                step.status === "completed" && "text-muted-foreground/70"
              )}
            >
              {step.status === "completed" ? (
                <Check className="w-3 h-3 text-green-500" />
              ) : step.status === "active" ? (
                <Loader2 className="w-3 h-3 animate-spin text-primary" />
              ) : (
                <div className="w-3 h-3 rounded-full border border-muted-foreground/30" />
              )}
              <span>{step.title}</span>
            </div>
          ))}
        </div>
      )}
    </div>
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
      "flex items-center gap-2 text-muted-foreground text-sm italic",
      className
    )}>
       <Loader2 className="w-3.5 h-3.5 animate-spin" />
       <span>AmaniQuery is thinking...</span>
    </div>
  )
}