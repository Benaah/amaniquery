"use client"

/**
 * Model Selector - WeKnora Integration
 * 
 * Allows users to switch between AI models dynamically
 */

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { 
  Sparkles, 
  Zap, 
  Brain, 
  Rocket,
  Info
} from "lucide-react"
import { cn } from "@/lib/utils"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface AIModel {
  id: string
  name: string
  provider: string
  description: string
  speed: 'fast' | 'medium' | 'slow'
  quality: 'standard' | 'high' | 'premium'
  icon: React.ReactNode
  available: boolean
}

// Prioritize Moonshot and Gemini (user has these APIs)
const AI_MODELS: AIModel[] = [
  {
    id: "moonshot-v1-8k",
    name: "Moonshot V1",
    provider: "Moonshot",
    description: "Fast, efficient for most queries",
    speed: "fast",
    quality: "high",
    icon: <Zap className="h-4 w-4" />,
    available: true
  },
  {
    id: "gemini-2.5-flash",
    name: "Gemini 2.5 Flash",
    provider: "Google",
    description: "Latest Gemini, great balance",
    speed: "fast",
    quality: "high",
    icon: <Sparkles className="h-4 w-4" />,
    available: true
  },
  {
    id: "gemini-1.5-pro",
    name: "Gemini 1.5 Pro",
    provider: "Google",
    description: "Best for complex analysis",
    speed: "medium",
    quality: "premium",
    icon: <Brain className="h-4 w-4" />,
    available: true
  },
  {
    id: "gpt-4o-mini",
    name: "GPT-4o Mini",
    provider: "OpenAI",
    description: "Requires OpenAI API key",
    speed: "fast",
    quality: "high",
    icon: <Sparkles className="h-4 w-4" />,
    available: false
  },
  {
    id: "claude-3.5-sonnet",
    name: "Claude 3.5 Sonnet",
    provider: "Anthropic",
    description: "Requires Anthropic API key",
    speed: "medium",
    quality: "premium",
    icon: <Rocket className="h-4 w-4" />,
    available: false
  }
]

interface ModelSelectorProps {
  selected: string
  onChange: (modelId: string) => void
  className?: string
  showDetails?: boolean
}

export function ModelSelector({
  selected,
  onChange,
  className,
  showDetails = true
}: ModelSelectorProps) {
  const selectedModel = AI_MODELS.find(m => m.id === selected) || AI_MODELS[0]

  const getSpeedBadge = (speed: string) => {
    switch (speed) {
      case 'fast': return <Badge variant="default" className="bg-green-500 text-xs">Fast</Badge>
      case 'medium': return <Badge variant="secondary" className="text-xs">Medium</Badge>
      case 'slow': return <Badge variant="outline" className="text-xs">Slow</Badge>
    }
  }

  const getQualityBadge = (quality: string) => {
    switch (quality) {
      case 'premium': return <Badge variant="default" className="bg-purple-500 text-xs">Premium</Badge>
      case 'high': return <Badge variant="secondary" className="text-xs">High</Badge>
      case 'standard': return <Badge variant="outline" className="text-xs">Standard</Badge>
    }
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Select value={selected} onValueChange={onChange}>
        <SelectTrigger className="w-[200px]">
          <div className="flex items-center gap-2">
            {selectedModel.icon}
            <SelectValue placeholder="Select model" />
          </div>
        </SelectTrigger>
        <SelectContent>
          {AI_MODELS.map((model) => (
            <SelectItem key={model.id} value={model.id}>
              <div className="flex items-center gap-2">
                {model.icon}
                <div className="flex flex-col">
                  <span className="font-medium">{model.name}</span>
                  <span className="text-xs text-muted-foreground">{model.provider}</span>
                </div>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      
      {showDetails && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Info className="h-4 w-4 text-muted-foreground" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-[250px]">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  {selectedModel.icon}
                  <span className="font-medium">{selectedModel.name}</span>
                </div>
                <p className="text-xs text-muted-foreground">{selectedModel.description}</p>
                <div className="flex gap-2">
                  {getSpeedBadge(selectedModel.speed)}
                  {getQualityBadge(selectedModel.quality)}
                </div>
              </div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </div>
  )
}

// Compact version for sidebar
export function ModelSelectorCompact({
  selected,
  onChange
}: {
  selected: string
  onChange: (modelId: string) => void
}) {
  const selectedModel = AI_MODELS.find(m => m.id === selected) || AI_MODELS[0]
  
  return (
    <Select value={selected} onValueChange={onChange}>
      <SelectTrigger className="w-full h-9">
        <div className="flex items-center gap-2 text-sm">
          {selectedModel.icon}
          <span>{selectedModel.name}</span>
        </div>
      </SelectTrigger>
      <SelectContent>
        {AI_MODELS.map((model) => (
          <SelectItem key={model.id} value={model.id}>
            <div className="flex items-center gap-2">
              {model.icon}
              <span>{model.name}</span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

export default ModelSelector
