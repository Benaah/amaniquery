import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { History, Search, Sparkles, Share2, Settings } from "lucide-react"
import Link from "next/link"

interface ChatHeaderProps {
  isResearchMode: boolean
  useHybrid: boolean
  currentSessionId: string | null
  showHistory: boolean
  isLoading: boolean
  onToggleHistory: () => void
  onToggleResearch: () => void
  onToggleHybrid: () => void
  onShare: () => void
}

export function ChatHeader({
  isResearchMode,
  useHybrid,
  currentSessionId,
  showHistory,
  isLoading,
  onToggleHistory,
  onToggleResearch,
  onToggleHybrid,
  onShare
}: ChatHeaderProps) {
  return (
    <div className="border-b border-white/5 bg-background/60 backdrop-blur-xl flex-shrink-0">
      <div className="flex flex-col gap-2 p-2 md:p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="md:hidden rounded-full h-8 w-8" onClick={onToggleHistory}>
              <History className="w-3.5 h-3.5" />
            </Button>
            <div>
              <p className="text-[10px] md:text-xs uppercase tracking-[0.2em] text-muted-foreground">AmaniQuery</p>
              <h1 className="text-base md:text-lg font-semibold">Conversational Legal Intelligence</h1>
            </div>
            {isResearchMode && (
              <Badge variant="default" className="bg-blue-600/90 text-xs py-0.5 px-2">
                <Search className="w-2.5 h-2.5 mr-1" />
                Research
              </Badge>
            )}
            {useHybrid && !isResearchMode && (
              <Badge variant="default" className="bg-purple-600/90 text-xs py-0.5 px-2">
                <Sparkles className="w-2.5 h-2.5 mr-1" />
                Hybrid
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1.5">
            <Button
              variant={useHybrid && !isResearchMode ? "default" : "outline"}
              size="sm"
              onClick={onToggleHybrid}
              disabled={isResearchMode}
              className={`h-7 rounded-full px-2 text-xs ${useHybrid && !isResearchMode ? "bg-purple-600 hover:bg-purple-700" : ""}`}
            >
              <Sparkles className="w-3 h-3 md:mr-1.5" />
              <span className="hidden md:inline">Hybrid</span>
            </Button>
            <Button
              variant={isResearchMode ? "default" : "outline"}
              size="sm"
              onClick={onToggleResearch}
              className={`h-7 rounded-full px-2 text-xs ${isResearchMode ? "bg-blue-600 hover:bg-blue-700" : ""}`}
            >
              <Search className="w-3 h-3 md:mr-1.5" />
              <span className="hidden md:inline">Research</span>
            </Button>
            {currentSessionId && (
              <Button variant="outline" size="sm" className="h-7 rounded-full px-2 text-xs" onClick={onShare}>
                <Share2 className="w-3 h-3 md:mr-1.5" />
                <span className="hidden md:inline">Share</span>
              </Button>
            )}
            <Link href="/">
              <Button variant="outline" size="sm" className="h-7 rounded-full px-2 text-xs">
                <Settings className="w-3 h-3 md:mr-1.5" />
                <span className="hidden md:inline">Home</span>
              </Button>
            </Link>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-1.5 text-[10px] md:text-xs">
          <div className="rounded-xl border border-white/10 bg-gradient-to-br from-primary/10 to-primary/5 px-2 py-1.5">
            <p className="text-muted-foreground uppercase tracking-wider text-[9px]">Streaming</p>
            <p className="font-semibold text-xs">Token-by-token</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/5 px-2 py-1.5">
            <p className="text-muted-foreground uppercase tracking-wider text-[9px]">Sources</p>
            <p className="font-semibold text-xs">Verifiable citations</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/5 px-2 py-1.5">
            <p className="text-muted-foreground uppercase tracking-wider text-[9px]">Mode</p>
            <p className="font-semibold text-xs">
              {isResearchMode ? "Deep research" : useHybrid ? "Hybrid RAG" : "Chat"}
            </p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/5 px-2 py-1.5">
            <p className="text-muted-foreground uppercase tracking-wider text-[9px]">Share</p>
            <p className="font-semibold text-xs">NiruShare ready</p>
          </div>
        </div>
      </div>
    </div>
  )
}
