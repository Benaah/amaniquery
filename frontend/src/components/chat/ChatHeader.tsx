import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { History, Search, Sparkles, Share2, Home } from "lucide-react"
import Link from "next/link"
import type { LucideIcon } from "lucide-react"

interface ChatHeaderProps {
  isResearchMode: boolean
  useHybrid: boolean
  currentSessionId: string | null
  showHistory: boolean
  isLoading: boolean
  onToggleHistory: () => void
  onToggleSidebar?: () => void
  onShare: () => void
  HistoryIcon?: LucideIcon
  mode?: "chat" | "hybrid" | "research"
}

export function ChatHeader({
  isResearchMode,
  useHybrid,
  currentSessionId,
  showHistory,
  onToggleHistory,
  onToggleSidebar,
  onShare,
  HistoryIcon,
  mode = "chat"
}: ChatHeaderProps) {
  return (
    <div className="border-b border-border bg-background flex-shrink-0 relative z-30 h-14 flex items-center">
      <div className="w-full px-4">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden -ml-2 h-9 w-9 text-muted-foreground"
              onClick={() => {
                if (onToggleSidebar) {
                  onToggleSidebar()
                } else {
                  onToggleHistory()
                }
              }}
            >
              {HistoryIcon ? <HistoryIcon className="w-5 h-5" /> : <History className="w-5 h-5" />}
            </Button>
            
            <div className="min-w-0 flex items-center gap-2">
              <span className="font-semibold text-sm md:text-base truncate">AmaniQuery</span>
              {/* Mode Indicator */}
              {mode && (
                <div className="flex items-center gap-1.5 px-2 py-1 bg-muted/60 rounded-lg border border-border/50">
                  <div className={`w-2 h-2 rounded-full ${
                    mode === "research" ? "bg-emerald-500" :
                    mode === "hybrid" ? "bg-purple-500" :
                    "bg-blue-500"
                  }`} />
                  <span className={`text-xs font-medium ${
                    mode === "research" ? "text-emerald-600 dark:text-emerald-400" :
                    mode === "hybrid" ? "text-purple-600 dark:text-purple-400" :
                    "text-blue-600 dark:text-blue-400"
                  }`}>
                    {mode === "research" ? "Deep Research" :
                     mode === "hybrid" ? "Hybrid RAG" :
                     "Standard Chat"}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1">
            {currentSessionId && (
              <Button variant="ghost" size="sm" className="h-8 text-muted-foreground hover:text-foreground" onClick={onShare}>
                <Share2 className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Share</span>
              </Button>
            )}
            <Link href="/">
              <Button variant="ghost" size="sm" className="h-8 text-muted-foreground hover:text-foreground">
                <Home className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
