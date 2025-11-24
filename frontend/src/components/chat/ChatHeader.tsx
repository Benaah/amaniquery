import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { History, Search, Sparkles, Share2, Home } from "lucide-react"
import Link from "next/link"

interface ChatHeaderProps {
  isResearchMode: boolean
  useHybrid: boolean
  currentSessionId: string | null
  showHistory: boolean
  isLoading: boolean
  onToggleHistory: () => void
  onShare: () => void
}

export function ChatHeader({
  isResearchMode,
  useHybrid,
  currentSessionId,
  showHistory,
  onToggleHistory,
  onShare
}: ChatHeaderProps) {
  return (
    <div className="border-b border-white/5 bg-background/60 backdrop-blur-xl flex-shrink-0 relative z-30">
      <div className="flex flex-col gap-1.5 md:gap-2 p-2 md:p-4">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 md:gap-2 min-w-0 flex-1">
            <div className="min-w-0 flex-1">
              <p className="text-[10px] md:text-xs uppercase tracking-[0.2em] text-muted-foreground truncate">AmaniQuery</p>
              <h1 className="text-sm md:text-lg font-semibold truncate">Conversational Legal Intelligence</h1>
            </div>
            {isResearchMode && (
              <Badge variant="default" className="bg-blue-600/90 text-[10px] md:text-xs py-0.5 px-1.5 md:px-2 flex-shrink-0">
                <Search className="w-2.5 h-2.5 mr-0.5 md:mr-1" />
                <span className="hidden sm:inline">Research</span>
              </Badge>
            )}
            {useHybrid && !isResearchMode && (
              <Badge variant="default" className="bg-purple-600/90 text-[10px] md:text-xs py-0.5 px-1.5 md:px-2 flex-shrink-0">
                <Sparkles className="w-2.5 h-2.5 mr-0.5 md:mr-1" />
                <span className="hidden sm:inline">Hybrid</span>
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1 md:gap-1.5 flex-shrink-0">
            <Button
              variant={showHistory ? "default" : "outline"}
              size="sm"
              className="h-9 md:h-7 rounded-full px-2 md:px-2.5 text-xs flex-shrink-0"
              onClick={onToggleHistory}
            >
              <History className="w-3.5 h-3.5 md:w-3 md:h-3 md:mr-1.5" />
              <span className="hidden md:inline">History</span>
            </Button>
            {currentSessionId && (
              <Button variant="outline" size="sm" className="h-9 md:h-7 rounded-full px-2 md:px-2.5 text-xs flex-shrink-0" onClick={onShare}>
                <Share2 className="w-3.5 h-3.5 md:w-3 md:h-3 md:mr-1.5" />
                <span className="hidden md:inline">Share</span>
              </Button>
            )}
            <Link href="/">
              <Button variant="outline" size="sm" className="h-9 md:h-7 rounded-full px-2 md:px-2.5 text-xs flex-shrink-0">
                <Home className="w-3.5 h-3.5 md:w-3 md:h-3 md:mr-1.5" />
                <span className="hidden md:inline">Home</span>
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
