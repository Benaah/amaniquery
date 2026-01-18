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
      <div className="mx-auto mb-4 md:mb-6 flex h-12 w-12 md:h-16 md:w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
        <Bot className="h-6 w-6 md:h-8 md:w-8 animate-pulse" />
      </div>
      <h2 className="text-xl md:text-3xl font-bold mb-2 md:mb-3 text-foreground px-2">
        Welcome to AmaniQuery
      </h2>
      {isResearchMode && (
        <Badge variant="secondary" className="mb-3 md:mb-4 text-xs py-1 px-2 md:px-3 bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
          <Search className="w-3 h-3 mr-1" />
          Research Mode
        </Badge>
      )}
      {useHybrid && !isResearchMode && (
        <Badge variant="secondary" className="mb-3 md:mb-4 text-xs py-1 px-2 md:px-3 bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">
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
      
      <div className="mt-8 md:mt-12 grid grid-cols-1 md:grid-cols-2 gap-3 max-w-3xl mx-auto px-2">
        {(isResearchMode ? RESEARCH_SUGGESTED_QUESTIONS : SUGGESTED_QUESTIONS).map((question) => (
          <button
            type="button"
            key={question.title}
            onClick={() => onSuggestionClick(question.title)}
            className="w-full rounded-2xl border border-border bg-card hover:bg-secondary/50 p-4 text-left transition-all duration-200 group min-h-[80px] shadow-sm hover:shadow-md"
          >
            <div className="flex items-start gap-3">
              <div className="rounded-xl bg-secondary p-2 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors flex-shrink-0">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-1 min-w-0">
                <p className="font-medium text-sm md:text-base leading-tight text-foreground">{question.title}</p>
                <p className="text-xs md:text-sm text-muted-foreground line-clamp-2">{question.description}</p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
