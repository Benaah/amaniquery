"use client"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { 
  Bot, 
  User, 
  Copy, 
  RotateCw, 
  ThumbsUp, 
  ThumbsDown,
  MoreVertical,
  ExternalLink,
  Check
} from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import type { Message, Source } from "./types"

interface AmaniMessageProps {
  message: Message
  onCopy: (content: string) => void
  onRegenerate: (messageId: string) => void
  onFeedback: (messageId: string, type: "like" | "dislike") => void
  isLoading?: boolean
  showFeedback?: boolean
}

interface InlineCitationProps {
  source: Source
  index: number
  onHover: (source: Source | null) => void
}

function InlineCitation({ source, index, onHover }: InlineCitationProps) {
  return (
    <sup
      className="inline-flex items-center justify-center w-5 h-5 text-xs font-medium text-primary bg-primary/10 rounded-full cursor-pointer hover:bg-primary/20 transition-colors ml-1"
      onMouseEnter={() => onHover(source)}
      onMouseLeave={() => onHover(null)}
      onClick={() => window.open(source.url, '_blank')}
    >
      {index}
    </sup>
  )
}

interface CitationTooltipProps {
  source: Source | null
  position: { x: number; y: number }
}

function CitationTooltip({ source, position }: CitationTooltipProps) {
  if (!source) return null

  return (
    <div 
      className="fixed z-50 bg-popover border rounded-lg shadow-lg p-3 max-w-sm"
      style={{ left: position.x, top: position.y }}
    >
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">{source.source_name}</span>
          <ExternalLink className="w-3 h-3 text-muted-foreground" />
        </div>
        <h4 className="text-sm font-medium leading-tight">{source.title}</h4>
        <p className="text-xs text-muted-foreground line-clamp-3">{source.excerpt}</p>
      </div>
    </div>
  )
}

function processContentWithCitations(content: string, sources?: Source[]) {
  if (!sources || sources.length === 0) return content

  let processedContent = content
  sources.forEach((source, index) => {
    const citationPattern = new RegExp(`\\[${index + 1}\\]`, 'g')
    processedContent = processedContent.replace(citationPattern, `{{CITATION:${index}}}`)
  })

  return processedContent
}

export function AmaniMessage({ 
  message, 
  onCopy, 
  onRegenerate, 
  onFeedback, 
  isLoading = false,
  showFeedback = true
}: AmaniMessageProps) {
  const [hoveredSource, setHoveredSource] = useState<Source | null>(null)
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 })
  const [hasCopied, setHasCopied] = useState(false)
  const [showActions, setShowActions] = useState(false)
  const messageRef = useRef<HTMLDivElement>(null)

  const isUser = message.role === "user"
  const hasFeedback = message.feedback_type !== undefined

  const handleCopy = async () => {
    await onCopy(message.content)
    setHasCopied(true)
    setTimeout(() => setHasCopied(false), 2000)
  }

  const handleSourceHover = (source: Source | null, event?: React.MouseEvent) => {
    setHoveredSource(source)
    if (source && event) {
      const rect = event.currentTarget.getBoundingClientRect()
      setTooltipPosition({
        x: rect.right + 10,
        y: rect.top
      })
    }
  }

  const renderContent = () => {
    const processedContent = processContentWithCitations(message.content, message.sources)
    const parts = processedContent.split(/(\{\{CITATION:\d+\}\})/g)

    return (
      <div className="space-y-4">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeHighlight]}
          components={{
            p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
            h1: ({ children }) => <h1 className="text-xl font-semibold mb-3 mt-4">{children}</h1>,
            h2: ({ children }) => <h2 className="text-lg font-semibold mb-2 mt-3">{children}</h2>,
            h3: ({ children }) => <h3 className="text-base font-semibold mb-2 mt-2">{children}</h3>,
            ul: ({ children }) => <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>,
            li: ({ children }) => <li className="mb-1">{children}</li>,
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-primary/20 pl-4 my-4 italic text-muted-foreground">
                {children}
              </blockquote>
            ),
            code: ({ inline, children, ...props }) => (
              inline ? (
                <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                  {children}
                </code>
              ) : (
                <code className="block bg-muted p-4 rounded-lg text-sm font-mono overflow-x-auto" {...props}>
                  {children}
                </code>
              )
            ),
          }}
        >
          {processedContent.replace(/\{\{CITATION:(\d+)\}\}/g, (match, index) => {
            const source = message.sources?.[parseInt(index)]
            return source ? `[${parseInt(index) + 1}]` : match
          })}
        </ReactMarkdown>

        {message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-2">
            {message.sources.map((source, index) => (
              <InlineCitation
                key={index}
                source={source}
                index={index + 1}
                onHover={(source) => handleSourceHover(source)}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div 
      ref={messageRef}
      className={cn(
        "group relative flex gap-4 p-4 rounded-2xl transition-all duration-200",
        isUser ? "flex-row-reverse" : "flex-row",
        isLoading && "opacity-75"
      )}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => {
        setShowActions(false)
        setHoveredSource(null)
      }}
    >
      {/* Avatar */}
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
        isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
      )}>
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          <Bot className="w-4 h-4" />
        )}
      </div>

      {/* Message Content */}
      <div className={cn(
        "flex-1 max-w-3xl space-y-3",
        isUser ? "text-right" : "text-left"
      )}>
        <div className={cn(
          "inline-block px-4 py-3 rounded-2xl",
          isUser 
            ? "bg-primary text-primary-foreground rounded-br-sm" 
            : "bg-muted rounded-bl-sm"
        )}>
          {renderContent()}
        </div>

        {/* Message Actions */}
        {showActions && !isUser && (
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-muted-foreground hover:text-foreground"
              onClick={handleCopy}
            >
              {hasCopied ? (
                <Check className="w-3 h-3" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-muted-foreground hover:text-foreground"
              onClick={() => onRegenerate(message.id)}
            >
              <RotateCw className="w-3 h-3" />
            </Button>

            {showFeedback && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  className={cn(
                    "h-7 px-2",
                    message.feedback_type === "like" 
                      ? "text-green-600 bg-green-50" 
                      : "text-muted-foreground hover:text-green-600"
                  )}
                  onClick={() => onFeedback(message.id, "like")}
                >
                  <ThumbsUp className="w-3 h-3" />
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  className={cn(
                    "h-7 px-2",
                    message.feedback_type === "dislike" 
                      ? "text-red-600 bg-red-50" 
                      : "text-muted-foreground hover:text-red-600"
                  )}
                  onClick={() => onFeedback(message.id, "dislike")}
                >
                  <ThumbsDown className="w-3 h-3" />
                </Button>
              </>
            )}

            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-muted-foreground hover:text-foreground"
            >
              <MoreVertical className="w-3 h-3" />
            </Button>
          </div>
        )}
      </div>

      {/* Citation Tooltip */}
      <CitationTooltip source={hoveredSource} position={tooltipPosition} />
    </div>
  )
}