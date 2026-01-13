"use client"

/**
 * Knowledge Base Selector
 * 
 * Allows users to select which knowledge bases to query
 */

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Database, Scale, Newspaper, FileText, ChevronDown, Check } from "lucide-react"
import { cn } from "@/lib/utils"

interface KnowledgeBase {
  id: string
  name: string
  description: string
  icon: React.ReactNode
  docCount?: number
  color: string
}

// Real namespaces from vector store
const KNOWLEDGE_BASES: KnowledgeBase[] = [
  {
    id: "kenya_law",
    name: "Kenya Law",
    description: "Constitution, Acts, Bills, Case Law",
    icon: <Scale className="h-4 w-4" />,
    color: "bg-blue-500"
  },
  {
    id: "kenya_news",
    name: "Kenya News",
    description: "Current affairs and news articles",
    icon: <Newspaper className="h-4 w-4" />,
    color: "bg-green-500"
  },
  {
    id: "parliament",
    name: "Parliament",
    description: "Bills, Hansard, Committee Reports",
    icon: <FileText className="h-4 w-4" />,
    color: "bg-purple-500"
  },
  {
    id: "general",
    name: "General",
    description: "General knowledge base",
    icon: <Database className="h-4 w-4" />,
    color: "bg-orange-500"
  }
]

interface KnowledgeBaseSelectorProps {
  selected: string[]
  onChange: (selected: string[]) => void
  className?: string
}

export function KnowledgeBaseSelector({
  selected,
  onChange,
  className
}: KnowledgeBaseSelectorProps) {
  const [open, setOpen] = useState(false)

  const toggleKnowledgeBase = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter(s => s !== id))
    } else {
      onChange([...selected, id])
    }
  }

  const selectAll = () => {
    onChange(KNOWLEDGE_BASES.map(kb => kb.id))
  }

  const clearAll = () => {
    onChange([])
  }

  const selectedKBs = KNOWLEDGE_BASES.filter(kb => selected.includes(kb.id))

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn("justify-between min-w-[200px]", className)}
        >
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <span>
              {selected.length === 0 
                ? "Select sources" 
                : selected.length === KNOWLEDGE_BASES.length 
                  ? "All sources"
                  : `${selected.length} sources`}
            </span>
          </div>
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[320px] p-0" align="start">
        <div className="border-b p-3 flex items-center justify-between">
          <span className="text-sm font-medium">Knowledge Bases</span>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={selectAll}>
              All
            </Button>
            <Button variant="ghost" size="sm" onClick={clearAll}>
              Clear
            </Button>
          </div>
        </div>
        <div className="p-2 space-y-1">
          {KNOWLEDGE_BASES.map((kb) => {
            const isSelected = selected.includes(kb.id)
            return (
              <div
                key={kb.id}
                className={cn(
                  "flex items-center gap-3 p-2 rounded-md cursor-pointer transition-colors",
                  isSelected ? "bg-accent" : "hover:bg-accent/50"
                )}
                onClick={() => toggleKnowledgeBase(kb.id)}
              >
                <Checkbox 
                  checked={isSelected}
                  onCheckedChange={() => toggleKnowledgeBase(kb.id)}
                />
                <div className={cn("p-1.5 rounded", kb.color, "text-white")}>
                  {kb.icon}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Label className="font-medium cursor-pointer">{kb.name}</Label>
                    {kb.docCount && (
                      <Badge variant="secondary" className="text-xs">
                        {(kb.docCount / 1000).toFixed(0)}k docs
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">{kb.description}</p>
                </div>
                {isSelected && <Check className="h-4 w-4 text-primary" />}
              </div>
            )
          })}
        </div>
        {selectedKBs.length > 0 && (
          <div className="border-t p-2">
            <div className="flex flex-wrap gap-1">
              {selectedKBs.map(kb => (
                <Badge 
                  key={kb.id} 
                  variant="secondary"
                  className="text-xs cursor-pointer"
                  onClick={() => toggleKnowledgeBase(kb.id)}
                >
                  {kb.name} ×
                </Badge>
              ))}
            </div>
          </div>
        )}
      </PopoverContent>
    </Popover>
  )
}

export default KnowledgeBaseSelector
