import { Bot, Search, Sparkles, ArrowUpRight } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { SUGGESTED_QUESTIONS, RESEARCH_SUGGESTED_QUESTIONS } from "./constants"

interface WelcomeScreenProps {
  isResearchMode: boolean
  useHybrid: boolean
  onSuggestionClick: (suggestion: string) => void
}

export function WelcomeScreen({
  isResearchMode,
  useHybrid,
  onSuggestionClick
}: WelcomeScreenProps) {
  return (
    <div className="text-center py-6 md:py-20 px-4 animate-in fade-in duration-500">
      <div className="mx-auto mb-4 md:mb-6 flex h-12 w-12 md:h-16 md:w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-primary/20 to-primary/10 border border-primary/20 backdrop-blur-xl">
        <Bot className="h-6 w-6 md:h-8 md:w-8 text-primary animate-pulse" />
      </div>
      <h2 className="text-xl md:text-3xl font-bold mb-2 md:mb-3 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent px-2">
        Welcome to AmaniQuery
      </h2>
      {isResearchMode && (
        <Badge variant="default" className="mb-3 md:mb-4 bg-blue-600/90 text-xs py-1 px-2 md:px-3">
          <Search className="w-3 h-3 mr-1" />
          Research Mode
        </Badge>
      )}
      {useHybrid && !isResearchMode && (
        <Badge variant="default" className="mb-3 md:mb-4 bg-purple-600/90 text-xs py-1 px-2 md:px-3">
          <Sparkles className="w-3 h-3 mr-1" />
          Hybrid Mode
        </Badge>
      )}
      <p className="text-muted-foreground mt-3 md:mt-4 text-xs md:text-base max-w-2xl mx-auto leading-relaxed px-2">
        {isResearchMode
          ? "Submit a detailed Kenyan legal question and receive structured analysis built for citations and downstream reporting."
          : useHybrid
          ? "Enhanced RAG with hybrid encoder and adaptive retrieval. Ask about Kenyan law, parliament, or current affairs with improved accuracy."
          : "Ask about Kenyan law, parliament, or current affairs. Answers stream in real time with sources you can trust."}
      </p>
      <div className="mt-4 md:mt-6 flex flex-wrap items-center justify-center gap-1.5 md:gap-2 text-[10px] md:text-xs text-muted-foreground px-2">
        <kbd className="px-1.5 md:px-2 py-0.5 md:py-1 rounded border border-white/10 bg-white/5">⌘K</kbd>
        <span>to focus input</span>
        <span className="mx-1 md:mx-2">•</span>
        <kbd className="px-1.5 md:px-2 py-0.5 md:py-1 rounded border border-white/10 bg-white/5">⌘↵</kbd>
        <span>to send</span>
      </div>
      <div className="mt-6 md:mt-8 grid grid-cols-1 md:grid-cols-2 gap-2.5 md:gap-3 max-w-3xl mx-auto px-2">
        {(isResearchMode ? RESEARCH_SUGGESTED_QUESTIONS : SUGGESTED_QUESTIONS).map((question) => (
          <button
            type="button"
            key={question.title}
            onClick={() => onSuggestionClick(question.title)}
            className="w-full rounded-3xl border border-white/10 bg-white/5 p-3 md:p-4 text-left transition hover:border-primary/40 hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 min-h-[60px]"
          >
            <div className="flex items-start gap-2 md:gap-3">
              <div className="rounded-2xl bg-primary/15 p-1.5 md:p-2 text-primary flex-shrink-0">
                <Sparkles className="w-3.5 h-3.5 md:w-4 md:h-4" />
              </div>
              <div className="flex-1 space-y-0.5 md:space-y-1 min-w-0">
                <p className="font-semibold text-xs md:text-base leading-tight break-words">{question.title}</p>
                <p className="text-[10px] md:text-sm text-muted-foreground break-words">{question.description}</p>
              </div>
              <ArrowUpRight className="w-3.5 h-3.5 md:w-4 md:h-4 text-muted-foreground flex-shrink-0" />
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
