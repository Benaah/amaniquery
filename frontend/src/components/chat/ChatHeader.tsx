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
}

export function ChatHeader({
  isResearchMode,
  useHybrid,
  currentSessionId,
  showHistory,
  onToggleHistory,
  onToggleSidebar,
  onShare,
  HistoryIcon
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
              {isResearchMode && (
                <Badge variant="secondary" className="text-xs font-normal bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border-0">
                  Research
                </Badge>
              )}
              {useHybrid && !isResearchMode && (
                <Badge variant="secondary" className="text-xs font-normal bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 border-0">
                  Hybrid
                </Badge>
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
