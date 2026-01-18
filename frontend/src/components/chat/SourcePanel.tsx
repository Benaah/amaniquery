"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Globe,
  BookOpen,
  FileText,
  Newspaper,
  GraduationCap,
  LinkIcon,
  Filter
} from "lucide-react"
import type { Source } from "./types"

interface SourcePanelProps {
  sources: Source[]
  isOpen: boolean
  onToggle: () => void
  className?: string
  variant?: "panel" | "inline" | "minimal"
  maxHeight?: string
}

interface SourceCardProps {
  source: Source
  index: number
  variant?: "detailed" | "compact" | "minimal-row"
  onView: (source: Source) => void
}

function getSourceIcon(category: string) {
  switch (category.toLowerCase()) {
    case "academic":
      return <GraduationCap className="w-3.5 h-3.5" />
    case "news":
      return <Newspaper className="w-3.5 h-3.5" />
    case "documentation":
      return <FileText className="w-3.5 h-3.5" />
    case "blog":
      return <BookOpen className="w-3.5 h-3.5" />
    default:
      return <Globe className="w-3.5 h-3.5" />
  }
}

function SourceCard({ source, index, variant = "detailed", onView }: SourceCardProps) {
  const handleClick = () => {
    window.open(source.url, '_blank', 'noopener,noreferrer')
    onView(source)
  }

  if (variant === "compact" || variant === "minimal-row") {
    return (
      <div 
        className="flex items-center gap-3 p-2.5 rounded-lg border border-transparent hover:bg-secondary/80 hover:border-border transition-all cursor-pointer group"
        onClick={handleClick}
      >
        <div className="flex-shrink-0 w-5 h-5 rounded-full bg-secondary text-muted-foreground group-hover:bg-background group-hover:text-foreground flex items-center justify-center text-[10px] font-medium border border-transparent group-hover:border-border transition-colors">
          {index + 1}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="text-muted-foreground/70">{getSourceIcon(source.category)}</span>
            <span className="text-[10px] uppercase tracking-wide text-muted-foreground/70 font-medium">{source.source_name}</span>
          </div>
          <h4 className="text-sm font-medium truncate text-foreground/90 group-hover:text-primary transition-colors">
            {source.title}
          </h4>
        </div>
      </div>
    )
  }

  // Detailed view (default) - heavily simplified
  return (
    <div className="group flex items-start gap-3 p-3 rounded-xl border border-transparent hover:bg-secondary/50 hover:border-border transition-all cursor-pointer" onClick={handleClick}>
      <div className="flex-shrink-0 w-6 h-6 rounded-md bg-secondary text-secondary-foreground flex items-center justify-center text-xs font-medium mt-0.5">
        {index + 1}
      </div>
      
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-medium leading-snug mb-1 group-hover:text-primary transition-colors">
            {source.title}
        </h4>
        
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
           <span className="flex items-center gap-1">
             {getSourceIcon(source.category)}
             {source.source_name}
           </span>
           <span>•</span>
           <span className="truncate max-w-[200px] opacity-70">{new URL(source.url).hostname.replace('www.', '')}</span>
        </div>
        
        {source.excerpt && (
            <p className="text-xs text-muted-foreground/80 line-clamp-2 mt-1.5 leading-relaxed">
              {source.excerpt}
            </p>
        )}
      </div>
    </div>
  )
}

export function SourcePanel({ 
  sources, 
  isOpen, 
  onToggle, 
  className, 
  variant = "panel",
  maxHeight = "400px"
}: SourcePanelProps) {
  const [viewedSources, setViewedSources] = useState<Set<string>>(new Set())
  const [filterCategory, setFilterCategory] = useState<string>("all")

  // Minimal inline variant (e.g. inside chat bubble)
  if (variant === "inline") {
    return (
      <div className={cn("mt-2", className)}>
        <Button
            variant="ghost"
            size="sm"
            className="h-7 px-0 text-xs text-muted-foreground hover:text-foreground font-normal hover:bg-transparent"
            onClick={onToggle}
          >
            {isOpen ? <ChevronDown className="w-3 h-3 mr-1.5" /> : <ChevronRight className="w-3 h-3 mr-1.5" />}
            {sources.length} Sources referenced
        </Button>
        
        {isOpen && (
          <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
            {sources.map((source, index) => (
              <SourceCard
                key={source.url}
                source={source}
                index={index}
                variant="compact"
                onView={(source) => setViewedSources(prev => new Set(prev).add(source.url))}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  if (variant === "minimal") {
    return (
      <div className={cn("flex items-center gap-2 flex-wrap", className)}>
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Sources</span>
        {sources.slice(0, 4).map((source, index) => (
          <button
            key={source.url}
            className="flex items-center gap-1.5 h-6 px-2 rounded-full bg-secondary hover:bg-secondary/80 text-[10px] font-medium transition-colors border border-transparent hover:border-border"
            onClick={() => window.open(source.url, '_blank', 'noopener,noreferrer')}
          >
            <span className="w-3.5 h-3.5 rounded-full bg-background flex items-center justify-center text-[9px]">{index + 1}</span>
            <span className="truncate max-w-[100px]">{source.source_name}</span>
          </button>
        ))}
        {sources.length > 4 && (
          <span className="text-xs text-muted-foreground">+{sources.length - 4} more</span>
        )}
      </div>
    )
  }

  // Panel variant (default)
  const categories = Array.from(new Set(sources.map(s => s.category)))
  const filteredSources = filterCategory === "all" 
    ? sources 
    : sources.filter(s => s.category === filterCategory)

  return (
    <div className={cn("border-t bg-background/50", className)}>
      <div className="p-3 flex items-center justify-between cursor-pointer hover:bg-secondary/30 transition-colors" onClick={onToggle}>
         <div className="flex items-center gap-2">
            {isOpen ? <ChevronDown className="w-4 h-4 text-muted-foreground" /> : <ChevronRight className="w-4 h-4 text-muted-foreground" />}
            <span className="text-sm font-medium">Sources & References</span>
            <Badge variant="secondary" className="text-xs h-5 px-1.5 min-w-[20px] justify-center bg-secondary text-secondary-foreground">
              {sources.length}
            </Badge>
         </div>
         {isOpen && categories.length > 1 && (
             <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                {categories.slice(0, 3).map(cat => (
                    <Badge key={cat} variant="outline" className="text-[10px] py-0 h-5 font-normal text-muted-foreground border-border bg-background">
                        {cat}
                    </Badge>
                ))}
             </div>
         )}
      </div>

      {isOpen && (
        <div className="px-3 pb-3 animate-in slide-in-from-top-2 duration-200">
           {categories.length > 1 && (
             <div className="flex flex-wrap gap-1.5 mb-3 px-1">
               <Button
                  variant={filterCategory === "all" ? "secondary" : "ghost"}
                  size="sm"
                  className="h-6 text-xs rounded-full"
                  onClick={() => setFilterCategory("all")}
                >
                  All
                </Button>
                {categories.map(category => (
                  <Button
                    key={category}
                    variant={filterCategory === category ? "secondary" : "ghost"}
                    size="sm"
                    className="h-6 text-xs rounded-full"
                    onClick={() => setFilterCategory(category)}
                  >
                    {category}
                  </Button>
                ))}
             </div>
           )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {filteredSources.map((source, index) => (
                <SourceCard
                  key={source.url}
                  source={source}
                  index={sources.indexOf(source)}
                  variant="detailed"
                  onView={(source) => setViewedSources(prev => new Set(prev).add(source.url))}
                />
              ))}
            </div>
        </div>
      )}
    </div>
  )
}

interface SourceSummaryProps {
  sources: Source[]
  className?: string
}

export function SourceSummary({ sources, className }: SourceSummaryProps) {
  if (!sources || sources.length === 0) return null

  return (
    <div className={cn("flex items-center gap-2 text-xs text-muted-foreground pl-1", className)}>
      <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
      <span>{sources.length} sources analyzed</span>
    </div>
  )
}