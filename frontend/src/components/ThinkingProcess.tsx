/**
 * Thinking Process Component
 * 
 * Displays the agent's reasoning path in a step-by-step expandable format
 * Similar to prominent LLM providers (Claude, o1, etc.)
 */

"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  ChevronDown, 
  ChevronRight,
  Brain,
  Check,
  Clock,
  Search,
  Lightbulb,
  AlertCircle,
  TrendingUp,
  Eye,
  Layers
} from "lucide-react"
import { cn } from "@/lib/utils"

// Types
interface ThoughtStep {
  step: number
  action: string
  observation: string
  reasoning: string
  duration_ms?: number
  confidence?: number
}

interface ReasoningPath {
  query: string
  thoughts: ThoughtStep[]
  total_duration_ms: number
  final_conclusion: string
}

interface ThinkingProcessProps {
  reasoning: ReasoningPath | string
  className?: string
  defaultExpanded?: boolean
}

export function ThinkingProcess({ 
  reasoning, 
  className, 
  defaultExpanded = false 
}: ThinkingProcessProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set())

  // Handle string reasoning (new format)
  if (typeof reasoning === 'string') {
    return (
      <Card className={cn("border-2 border-primary/20", className)}>
        <CardHeader 
          className="cursor-pointer hover:bg-accent/50 transition-colors py-3"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              <CardTitle className="text-base">Thinking Process</CardTitle>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="secondary" className="font-mono text-xs">
                Analysis
              </Badge>
              {isExpanded ? (
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              )}
            </div>
          </div>
        </CardHeader>

        {isExpanded && (
          <CardContent className="pt-0 pb-4">
            <ScrollArea className="max-h-[400px]">
              <div className="bg-muted/30 p-4 rounded-lg text-sm text-muted-foreground whitespace-pre-wrap font-mono leading-relaxed">
                {reasoning}
              </div>
            </ScrollArea>
          </CardContent>
        )}
      </Card>
    )
  }

  // Handle structured reasoning (legacy/future format)
  const toggleStep = (step: number) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(step)) {
      newExpanded.delete(step)
    } else {
      newExpanded.add(step)
    }
    setExpandedSteps(newExpanded)
  }

  const toggleAll = () => {
    if (isExpanded) {
      setIsExpanded(false)
      setExpandedSteps(new Set())
    } else {
      setIsExpanded(true)
      setExpandedSteps(new Set(reasoning.thoughts.map(t => t.step)))
    }
  }

  return (
    <Card className={cn("border-2 border-primary/20", className)}>
      <CardHeader 
        className="cursor-pointer hover:bg-accent/50 transition-colors"
        onClick={toggleAll}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Thinking Process</CardTitle>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="secondary" className="font-mono">
              {reasoning.thoughts.length} steps
            </Badge>
            <Badge variant="outline" className="font-mono">
              {reasoning.total_duration_ms}ms
            </Badge>
            {isExpanded ? (
              <ChevronDown className="h-5 w-5 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-5 w-5 text-muted-foreground" />
            )}
          </div>
        </div>
        <CardDescription className="mt-2">
          Step-by-step reasoning for: <span className="font-medium">{reasoning.query}</span>
        </CardDescription>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-0">
          <ScrollArea className="max-h-[600px]">
            <div className="space-y-3 relative">
              {/* Timeline line */}
              <div className="absolute left-[17px] top-4 bottom-4 w-[2px] bg-border" />

              {reasoning.thoughts.map((thought, idx) => (
                <ThoughtStepCard
                  key={thought.step}
                  thought={thought}
                  isExpanded={expandedSteps.has(thought.step)}
                  onToggle={() => toggleStep(thought.step)}
                  isLast={idx === reasoning.thoughts.length - 1}
                />
              ))}

              {/* Final Conclusion */}
              <div className="ml-12 p-4 rounded-lg bg-primary/5 border-2 border-primary/20">
                <div className="flex items-center gap-2 mb-2">
                  <Check className="h-5 w-5 text-green-500" />
                  <h4 className="font-semibold">Conclusion</h4>
                </div>
                <p className="text-sm text-muted-foreground">{reasoning.final_conclusion}</p>
              </div>
            </div>
          </ScrollArea>
        </CardContent>
      )}
    </Card>
  )
}

// Individual Thought Step Card
function ThoughtStepCard({
  thought,
  isExpanded,
  onToggle,
  isLast
}: {
  thought: ThoughtStep
  isExpanded: boolean
  onToggle: () => void
  isLast: boolean
}) {
  const getActionIcon = (action: string) => {
    const actionLower = action.toLowerCase()
    if (actionLower.includes("search") || actionLower.includes("retriev")) {
      return <Search className="h-4 w-4" />
    }
    if (actionLower.includes("analyz") || actionLower.includes("check")) {
      return <Eye className="h-4 w-4" />
    }
    if (actionLower.includes("reason") || actionLower.includes("think")) {
      return <Lightbulb className="h-4 w-4" />
    }
    if (actionLower.includes("synthesiz") || actionLower.includes("combin")) {
      return <Layers className="h-4 w-4" />
    }
    return <TrendingUp className="h-4 w-4" />
  }

  return (
    <div className="relative">
      {/* Step number bubble */}
      <div className="absolute left-0 top-3 w-[34px] h-[34px] rounded-full bg-primary flex items-center justify-center text-white font-bold text-sm z-10">
        {thought.step}
      </div>

      {/* Step card */}
      <div className="ml-12 relative">
        <div 
          className={cn(
            "border rounded-lg transition-all cursor-pointer",
            isExpanded ? "bg-accent/50 border-primary/30" : "bg-card hover:bg-accent/30"
          )}
          onClick={onToggle}
        >
          {/* Header */}
          <div className="p-3 flex items-center justify-between">
            <div className="flex items-center gap-2 flex-1">
              {getActionIcon(thought.action)}
              <span className="font-medium text-sm">{thought.action}</span>
            </div>
            <div className="flex items-center gap-2">
              {thought.duration_ms && (
                <Badge variant="outline" className="text-xs font-mono">
                  <Clock className="h-3 w-3 mr-1" />
                  {thought.duration_ms}ms
                </Badge>
              )}
              {thought.confidence !== undefined && (
                <Badge 
                  variant={thought.confidence >= 0.8 ? "default" : "secondary"}
                  className="text-xs font-mono"
                >
                  {(thought.confidence * 100).toFixed(0)}%
                </Badge>
              )}
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          </div>

          {/* Expanded content */}
          {isExpanded && (
            <div className="px-3 pb-3 space-y-3 border-t">
              {/* Observation */}
              <div className="pt-3">
                <div className="flex items-center gap-2 mb-1">
                  <Eye className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    Observation
                  </span>
                </div>
                <p className="text-sm ml-5">{thought.observation}</p>
              </div>

              {/* Reasoning */}
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Lightbulb className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    Reasoning
                  </span>
                </div>
                <p className="text-sm ml-5 text-muted-foreground">{thought.reasoning}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Compact version for inline display
export function ThinkingProcessCompact({ 
  reasoning 
}: { 
  reasoning: ReasoningPath 
}) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="border-l-2 border-primary/20 pl-4 py-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm font-medium hover:text-primary transition-colors"
      >
        <Brain className="h-4 w-4" />
        <span>View thinking process ({reasoning.thoughts.length} steps)</span>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-3 space-y-2">
          {reasoning.thoughts.map((thought) => (
            <div key={thought.step} className="text-sm">
              <span className="font-semibold">{thought.step}.</span> {thought.action}
              <p className="text-muted-foreground ml-4 text-xs">{thought.observation}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Loading skeleton
export function ThinkingProcessSkeleton() {
  return (
    <Card className="border-2 border-primary/20">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary animate-pulse" />
            <CardTitle className="text-lg">Thinking...</CardTitle>
          </div>
          <Badge variant="secondary" className="animate-pulse">
            Processing
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 animate-pulse" />
              <div className="flex-1 h-12 bg-accent/50 rounded-lg animate-pulse" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default ThinkingProcess
