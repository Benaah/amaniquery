"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
  AcademicCap,
  LinkIcon,
  Eye,
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
  variant?: "detailed" | "compact"
  onView: (source: Source) => void
}

function getSourceIcon(category: string) {
  switch (category.toLowerCase()) {
    case "academic":
      return <AcademicCap className="w-4 h-4" />
    case "news":
      return <Newspaper className="w-4 h-4" />
    case "documentation":
      return <FileText className="w-4 h-4" />
    case "blog":
      return <BookOpen className="w-4 h-4" />
    default:
      return <Globe className="w-4 h-4" />
  }
}

function getCategoryColor(category: string) {
  switch (category.toLowerCase()) {
    case "academic":
      return "bg-blue-100 text-blue-800 border-blue-200"
    case "news":
      return "bg-red-100 text-red-800 border-red-200"
    case "documentation":
      return "bg-green-100 text-green-800 border-green-200"
    case "blog":
      return "bg-purple-100 text-purple-800 border-purple-200"
    default:
      return "bg-gray-100 text-gray-800 border-gray-200"
  }
}

function SourceCard({ source, index, variant = "detailed", onView }: SourceCardProps) {
  const handleClick = () => {
    window.open(source.url, '_blank', 'noopener,noreferrer')
    onView(source)
  }

  if (variant === "compact") {
    return (
      <div 
        className="flex items-center gap-3 p-3 rounded-lg border hover:bg-accent/50 transition-colors cursor-pointer group"
        onClick={handleClick}
      >
        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium text-primary">
          {index + 1}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-muted-foreground">{getSourceIcon(source.category)}</span>
            <span className="text-xs text-muted-foreground">{source.source_name}</span>
          </div>
          <h4 className="text-sm font-medium truncate group-hover:text-primary transition-colors">
            {source.title}
          </h4>
        </div>
        <ExternalLink className="w-3 h-3 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0" />
      </div>
    )
  }

  return (
    <Card className="border hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
            <span className="text-sm font-medium text-primary">{index + 1}</span>
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="secondary" className={cn("text-xs", getCategoryColor(source.category))}>
                {getSourceIcon(source.category)}
                <span className="ml-1">{source.category}</span>
              </Badge>
              <span className="text-xs text-muted-foreground">{source.source_name}</span>
            </div>
            
            <h4 className="text-sm font-medium mb-2 line-clamp-2 hover:text-primary transition-colors">
              <button
                onClick={handleClick}
                className="text-left hover:underline"
              >
                {source.title}
              </button>
            </h4>
            
            <p className="text-xs text-muted-foreground line-clamp-3 mb-3">
              {source.excerpt}
            </p>
            
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
              onClick={handleClick}
            >
              <ExternalLink className="w-3 h-3 mr-1" />
              View Source
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
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

  if (variant === "inline") {
    return (
      <div className={cn("bg-muted/50 rounded-lg p-3", className)}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <LinkIcon className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">Sources</span>
            <Badge variant="secondary" className="text-xs">
              {sources.length}
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={onToggle}
          >
            {isOpen ? (
              <>
                <ChevronDown className="w-3 h-3 mr-1" />
                Hide
              </>
            ) : (
              <>
                <ChevronRight className="w-3 h-3 mr-1" />
                Show
              </>
            )}
          </Button>
        </div>
        
        {isOpen && (
          <div className="space-y-2">
            {sources.slice(0, 3).map((source, index) => (
              <SourceCard
                key={source.url}
                source={source}
                index={index}
                variant="compact"
                onView={(source) => setViewedSources(prev => new Set(prev).add(source.url))}
              />
            ))}
            {sources.length > 3 && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full h-8 text-xs text-muted-foreground"
                onClick={onToggle}
              >
                View {sources.length - 3} more sources
              </Button>
            )}
          </div>
        )}
      </div>
    )
  }

  if (variant === "minimal") {
    return (
      <div className={cn("flex items-center gap-2 flex-wrap", className)}>
        <LinkIcon className="w-4 h-4 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Sources:</span>
        {sources.slice(0, 5).map((source, index) => (
          <Button
            key={source.url}
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => window.open(source.url, '_blank', 'noopener,noreferrer')}
          >
            {index + 1}. {source.source_name}
          </Button>
        ))}
        {sources.length > 5 && (
          <Badge variant="secondary" className="text-xs">
            +{sources.length - 5} more
          </Badge>
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
    <Card className={cn("border-2", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-lg">Sources</CardTitle>
            <Badge variant="secondary" className="text-sm">
              {sources.length}
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2"
            onClick={onToggle}
          >
            {isOpen ? (
              <>
                <ChevronDown className="w-4 h-4 mr-1" />
                Collapse
              </>
            ) : (
              <>
                <ChevronRight className="w-4 h-4 mr-1" />
                Expand
              </>
            )}
          </Button>
        </div>
        
        {categories.length > 1 && (
          <div className="flex items-center gap-2 mt-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <div className="flex gap-1 flex-wrap">
              <Button
                variant={filterCategory === "all" ? "secondary" : "ghost"}
                size="sm"
                className="h-6 px-2 text-xs"
                onClick={() => setFilterCategory("all")}
              >
                All
              </Button>
              {categories.map(category => (
                <Button
                  key={category}
                  variant={filterCategory === category ? "secondary" : "ghost"}
                  size="sm"
                  className="h-6 px-2 text-xs"
                  onClick={() => setFilterCategory(category)}
                >
                  {category}
                </Button>
              ))}
            </div>
          </div>
        )}
      </CardHeader>

      {isOpen && (
        <CardContent className="pt-0">
          <ScrollArea className={maxHeight}>
            <div className="space-y-3">
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
          </ScrollArea>
        </CardContent>
      )}
    </Card>
  )
}

interface SourceSummaryProps {
  sources: Source[]
  className?: string
}

export function SourceSummary({ sources, className }: SourceSummaryProps) {
  if (!sources || sources.length === 0) return null

  const categories = Array.from(new Set(sources.map(s => s.category)))
  const sourcesByCategory = categories.map(category => ({
    category,
    count: sources.filter(s => s.category === category).length,
    sources: sources.filter(s => s.category === category)
  }))

  return (
    <div className={cn("flex items-center gap-3 text-sm text-muted-foreground", className)}>
      <LinkIcon className="w-4 h-4" />
      <span>Based on {sources.length} sources</span>
      {sourcesByCategory.map(({ category, count }) => (
        <Badge
          key={category}
          variant="outline"
          className="text-xs"
        >
          {getSourceIcon(category)}
          <span className="ml-1">{count} {category}</span>
        </Badge>
      ))}
    </div>
  )
}