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
    <div className="text-center py-10 md:py-20 animate-in fade-in duration-500">
      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-primary/20 to-primary/10 border border-primary/20 backdrop-blur-xl">
        <Bot className="h-8 w-8 text-primary animate-pulse" />
      </div>
      <h2 className="text-2xl md:text-3xl font-bold mb-3 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
        Welcome to AmaniQuery
      </h2>
      {isResearchMode && (
        <Badge variant="default" className="mb-4 bg-blue-600/90 text-xs py-1 px-3">
          <Search className="w-3 h-3 mr-1" />
          Research Mode
        </Badge>
      )}
      {useHybrid && !isResearchMode && (
        <Badge variant="default" className="mb-4 bg-purple-600/90 text-xs py-1 px-3">
          <Sparkles className="w-3 h-3 mr-1" />
          Hybrid Mode
        </Badge>
      )}
      <p className="text-muted-foreground mt-4 text-sm md:text-base max-w-2xl mx-auto leading-relaxed">
        {isResearchMode
          ? "Submit a detailed Kenyan legal question and receive structured analysis built for citations and downstream reporting."
          : useHybrid
          ? "Enhanced RAG with hybrid encoder and adaptive retrieval. Ask about Kenyan law, parliament, or current affairs with improved accuracy."
          : "Ask about Kenyan law, parliament, or current affairs. Answers stream in real time with sources you can trust."}
      </p>
      <div className="mt-6 flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <kbd className="px-2 py-1 rounded border border-white/10 bg-white/5">⌘K</kbd>
        <span>to focus input</span>
        <span className="mx-2">•</span>
        <kbd className="px-2 py-1 rounded border border-white/10 bg-white/5">⌘↵</kbd>
        <span>to send</span>
      </div>
      <div className="mt-8 grid gap-3 md:grid-cols-2 max-w-3xl mx-auto">
        {(isResearchMode ? RESEARCH_SUGGESTED_QUESTIONS : SUGGESTED_QUESTIONS).map((question) => (
          <button
            type="button"
            key={question.title}
            onClick={() => onSuggestionClick(question.title)}
            className="w-full rounded-3xl border border-white/10 bg-white/5 p-4 text-left transition hover:border-primary/40 hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60"
          >
            <div className="flex items-start gap-3">
              <div className="rounded-2xl bg-primary/15 p-2 text-primary">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-1">
                <p className="font-semibold text-sm md:text-base leading-tight">{question.title}</p>
                <p className="text-xs text-muted-foreground md:text-sm">{question.description}</p>
              </div>
              <ArrowUpRight className="w-4 h-4 text-muted-foreground" />
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
