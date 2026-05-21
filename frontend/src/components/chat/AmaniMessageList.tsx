"use client"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { AmaniMessage } from "./AmaniMessage"
import { MessageActions } from "./MessageActions"
import { ThinkingIndicator, CompactThinkingIndicator } from "./ThinkingIndicator"
import { SourcePanel, SourceSummary } from "./SourcePanel"
import { WelcomeScreen } from "./WelcomeScreen"
import { Loader2, Square, Search, Globe, Newspaper, Calculator, Link as LinkIcon, Youtube, Twitter, FileText, Mail, BookOpen, Hash, CheckCircle2, XCircle, Clock } from "lucide-react"
import type { StreamToolEvent } from "./types"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { ShareSheet } from "./ShareSheet"
import type { Message, ShareSheetState, SharePlatform, Source } from "./types"

interface AmaniMessageListProps {
  messages: Message[]
  isLoading: boolean
  isThinking?: boolean
  thinkingSteps?: any[]
  onSendMessage: (content: string) => void
  onRegenerate: (messageId: string) => void
  onFeedback: (messageId: string, type: "like" | "dislike") => void
  onCopy: (content: string) => void
  onShare: (message: Message) => void
  onGeneratePDF?: (messageId: string) => void
  onGenerateWord?: (messageId: string) => void
  showWelcomeScreen?: boolean
  className?: string
  showInlineSources?: boolean
  enableThinkingIndicator?: boolean
  messageClassName?: string
  shareSheet?: ShareSheetState | null
  onCloseShareSheet?: () => void
  onChangeSharePlatform?: (message: Message, platform: SharePlatform) => void
  onCopyShareContent?: () => void
  onGenerateShareImage?: (message: Message) => void
  onOpenShareIntent?: (message: Message) => void
  onAuthenticatePlatform?: (platform: SharePlatform) => void
  onPostDirectly?: (message: Message) => void
  platformTokens?: Record<SharePlatform, string | null>
  editingMessageId?: string | null
  editingContent?: string
  setEditingContent?: (content: string) => void
  onSaveEdit?: (messageId: string) => void
  onCancelEdit?: () => void
  onStartEdit?: (message: Message) => void
  onCopyFailedQuery?: (message: Message) => void
  onEditFailedQuery?: (message: Message) => void
  onResendFailedQuery?: (message: Message) => void
  isStreaming?: boolean
  streamingContent?: string
  streamingSources?: Source[]
  streamingTools?: StreamToolEvent[]
  onAbortStream?: () => void
}

// =============================================================================
// TOOL EVENT HELPERS
// =============================================================================

function ToolIcon({ toolName }: { toolName: string }) {
  const iconClass = "w-3.5 h-3.5 text-muted-foreground"
  switch (toolName) {
    case "kb_search": return <BookOpen className={iconClass} />
    case "web_search": return <Globe className={iconClass} />
    case "news_search": return <Newspaper className={iconClass} />
    case "calculator": case "fees_calculator": return <Calculator className={iconClass} />
    case "url_fetch": return <LinkIcon className={iconClass} />
    case "youtube_search": return <Youtube className={iconClass} />
    case "twitter_search": return <Twitter className={iconClass} />
    case "file_write": return <FileText className={iconClass} />
    case "email_draft": return <Mail className={iconClass} />
    case "bill_status": case "hansard": return <Hash className={iconClass} />
    case "legal_citation": return <BookOpen className={iconClass} />
    default: return <Search className={iconClass} />
  }
}

function _getToolLabel(tool: StreamToolEvent): string {
  if (tool.type === "tool_start") {
    switch (tool.tool_name) {
      case "kb_search": return "Searching knowledge base..."
      case "web_search": return "Searching the web..."
      case "news_search": return "Searching news..."
      case "calculator": return "Calculating..."
      case "fees_calculator": return "Computing fees..."
      case "url_fetch": return "Fetching URL..."
      case "youtube_search": return "Searching YouTube..."
      case "twitter_search": return "Searching X/Twitter..."
      case "file_write": return "Writing file..."
      case "email_draft": return "Drafting email..."
      case "bill_status": return "Looking up bill status..."
      case "hansard": return "Retrieving debates..."
      case "legal_citation": return "Formatting citation..."
      default: return `Running ${tool.tool_name}...`
    }
  }
  if (tool.type === "tool_result") {
    if (tool.status === "success") return `${tool.tool_name} completed`
    if (tool.status === "cached") return `${tool.tool_name} (cached)`
    if (tool.status === "error") return `${tool.tool_name} failed`
    if (tool.status === "timeout") return `${tool.tool_name} timed out`
    return `${tool.tool_name} done`
  }
  return tool.tool_name
}

function _formatMs(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}


interface MessageGroup {
  id: string
  messages: Message[]
  hasAssistantResponse: boolean
  isComplete: boolean
}

export function AmaniMessageList({
  messages,
  isLoading,
  isThinking = false,
  thinkingSteps = [],
  onSendMessage,
  onRegenerate,
  onFeedback,
  onCopy,
  onShare,
  onGeneratePDF,
  onGenerateWord,
  showWelcomeScreen = false,
  className,
  showInlineSources = true,
  enableThinkingIndicator = true,
  messageClassName,
  shareSheet,
  onCloseShareSheet,
  onChangeSharePlatform,
  onCopyShareContent,
  onGenerateShareImage,
  onOpenShareIntent,
  onAuthenticatePlatform,
  onPostDirectly,
  platformTokens,
  editingMessageId,
  editingContent,
  setEditingContent,
  onSaveEdit,
  onCancelEdit,
  onStartEdit,
  onCopyFailedQuery,
  onEditFailedQuery,
  onResendFailedQuery,
  isStreaming = false,
  streamingContent = "",
  streamingSources = [],
  streamingTools = [],
  onAbortStream
}: AmaniMessageListProps) {
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({})
  const [expandedThinking, setExpandedThinking] = useState<Record<string, boolean>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  // Group messages into conversation turns
  const messageGroups: MessageGroup[] = []
  let currentGroup: MessageGroup | null = null

  messages.forEach((message, index) => {
    if (message.role === "user") {
      // Start new group for user message
      if (currentGroup) {
        messageGroups.push(currentGroup)
      }
      currentGroup = {
        id: message.id,
        messages: [message],
        hasAssistantResponse: false,
        isComplete: false
      }
    } else if (message.role === "assistant" && currentGroup) {
      // Add assistant message to current group
      currentGroup.messages.push(message)
      currentGroup.hasAssistantResponse = true
      currentGroup.isComplete = !message.isRegenerating && !isLoading
    }
  })

  // Add the last group if it exists
  if (currentGroup) {
    messageGroups.push(currentGroup)
  }

  const toggleSources = (groupId: string) => {
    setExpandedSources(prev => ({
      ...prev,
      [groupId]: !prev[groupId]
    }))
  }

  const toggleThinking = (groupId: string) => {
    setExpandedThinking(prev => ({
      ...prev,
      [groupId]: !prev[groupId]
    }))
  }

  if (showWelcomeScreen && messages.length === 0) {
    return (
      <div className={cn("flex-1 flex items-center justify-center", className)}>
        <WelcomeScreen 
          onSuggestionClick={onSendMessage}
          isResearchMode={false}
          useHybrid={false}
        />
      </div>
    )
  }

  return (
    <div ref={containerRef} className={cn("flex-1 overflow-y-auto", className)}>
      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {messageGroups.map((group) => {
          const userMessage = group.messages.find(m => m.role === "user")
          const assistantMessage = group.messages.find(m => m.role === "assistant")
          const showThinking = enableThinkingIndicator && 
                             group.hasAssistantResponse && 
                             assistantMessage?.isRegenerating

          return (
            <div key={group.id} className="space-y-4">
              {/* User Message */}
              {userMessage && (
                <div className={cn("animate-in fade-in duration-300", messageClassName)}>
                  <AmaniMessage
                    message={userMessage}
                    onCopy={onCopy}
                    onRegenerate={onRegenerate}
                    onFeedback={onFeedback}
                    showFeedback={false}
                    isEditing={editingMessageId === userMessage.id}
                    editingContent={editingContent}
                    onEditChange={setEditingContent}
                    onSaveEdit={onSaveEdit}
                    onCancelEdit={onCancelEdit}
                    onStartEdit={onStartEdit}
                    onCopyFailed={onCopyFailedQuery}
                    onEditFailed={onEditFailedQuery}
                    onResendFailed={onResendFailedQuery}
                  />
                  {shareSheet && shareSheet.messageId === userMessage.id && (
                      <ShareSheet
                        message={userMessage}
                        shareSheet={shareSheet}
                        onClose={onCloseShareSheet!}
                        onChangePlatform={onChangeSharePlatform!}
                        onCopyContent={onCopyShareContent!}
                        onGenerateImage={onGenerateShareImage!}
                        onOpenIntent={onOpenShareIntent!}
                        onAuthenticate={onAuthenticatePlatform!}
                        onPostDirectly={onPostDirectly!}
                        platformTokens={platformTokens!}
                      />
                  )}
                </div>
              )}

              {/* Assistant Response Area */}
              {group.hasAssistantResponse && assistantMessage && (
                <div className={cn("space-y-3 animate-in fade-in duration-500", messageClassName)}>
                  {/* Thinking Indicator */}
                  {showThinking && (
                    <div className="ml-12">
                      <ThinkingIndicator
                        isActive={showThinking}
                        defaultExpanded={expandedThinking[group.id]}
                        onToggle={(expanded) => toggleThinking(group.id)}
                        className="mb-3"
                      />
                    </div>
                  )}

                  {/* Assistant Message */}
                  <div className="relative group">
                    <AmaniMessage
                      message={assistantMessage}
                      onCopy={onCopy}
                      onRegenerate={onRegenerate}
                      onFeedback={onFeedback}
                      isLoading={assistantMessage.isRegenerating}
                    />
                    
                    {/* Message Actions */}
                    <div className="absolute -right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <MessageActions
                        message={assistantMessage}
                        onCopy={onCopy}
                        onRegenerate={onRegenerate}
                        onFeedback={onFeedback}
                        onShare={onShare}
                        onGeneratePDF={onGeneratePDF}
                        onGenerateWord={onGenerateWord}
                        compact={true}
                        className="bg-card/80 backdrop-blur-sm rounded-lg border shadow-sm"
                      />
                    </div>
                  </div>

                  {/* Inline Sources */}
                  {showInlineSources && assistantMessage.sources && assistantMessage.sources.length > 0 && (
                    <div className="ml-12">
                      <SourcePanel
                        sources={assistantMessage.sources}
                        isOpen={expandedSources[group.id] || false}
                        onToggle={() => toggleSources(group.id)}
                        variant="inline"
                      />
                    </div>
                  )}

                  {/* Source Summary */}
                  {!showInlineSources && assistantMessage.sources && assistantMessage.sources.length > 0 && (
                    <div className="ml-12">
                      <SourceSummary
                        sources={assistantMessage.sources}
                        className="text-xs"
                      />
                    </div>
                  )}

                  {/* Share Sheet */}
                  {shareSheet && shareSheet.messageId === assistantMessage.id && (
                      <div className="ml-12">
                        <ShareSheet
                            message={assistantMessage}
                            shareSheet={shareSheet}
                            onClose={onCloseShareSheet!}
                            onChangePlatform={onChangeSharePlatform!}
                            onCopyContent={onCopyShareContent!}
                            onGenerateImage={onGenerateShareImage!}
                            onOpenIntent={onOpenShareIntent!}
                            onAuthenticate={onAuthenticatePlatform!}
                            onPostDirectly={onPostDirectly!}
                            platformTokens={platformTokens!}
                        />
                      </div>
                  )}
                </div>
              )}

              {/* Loading / Streaming State for Current Response */}
              {!group.hasAssistantResponse && isLoading && group === messageGroups[messageGroups.length - 1] && (
                <div className="ml-12 space-y-3 animate-in fade-in duration-500">
                  {enableThinkingIndicator && (
                    <CompactThinkingIndicator isActive={isThinking} />
                  )}
                  {/* Tool Execution Events (Gemini-style tool cards) */}
                  {isStreaming && streamingTools.length > 0 && (
                    <div className="space-y-2 mb-3">
                      {streamingTools.map((tool, i) => (
                        <div
                          key={`${tool.tool_name}-${i}`}
                          className="flex items-center gap-2.5 px-3 py-2 bg-muted/50 border border-border/50 rounded-lg animate-in fade-in slide-in-from-left-2 duration-200"
                        >
                          <ToolIcon toolName={tool.tool_name} />
                          <span className="text-sm text-muted-foreground flex-1 truncate">{_getToolLabel(tool)}</span>
                          {tool.type === "tool_start" && (
                            <div className="w-3.5 h-3.5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                          )}
                          {tool.type === "tool_result" && tool.status === "success" && (
                            <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                          )}
                          {tool.type === "tool_result" && tool.status === "error" && (
                            <XCircle className="w-3.5 h-3.5 text-red-500" />
                          )}
                          {tool.type === "tool_result" && tool.latency_ms != null && (
                            <span className="text-[11px] text-muted-foreground/60 tabular-nums">
                              {_formatMs(tool.latency_ms)}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {isStreaming && streamingContent ? (
                    <div className="flex items-start gap-3 p-4 bg-muted rounded-2xl animate-in fade-in duration-300">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              p: ({ children }) => <span className="block mb-2 leading-7">{children}</span>,
                              code: ({ children, className }) => {
                                const match = /language-(\w+)/.exec(className || "")
                                const isInline = !match && !String(children).includes("\n")
                                return isInline ? (
                                  <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono">{children}</code>
                                ) : (
                                  <div className="my-2 rounded border border-border bg-muted/50 p-3 overflow-x-auto">
                                    <code className="text-sm font-mono">{children}</code>
                                  </div>
                                )
                              },
                            }}
                          >
                            {streamingContent}
                          </ReactMarkdown>
                          <span className="inline-block w-2 h-4 bg-primary rounded-sm animate-pulse ml-0.5 align-text-bottom" />
                        </div>
                        {streamingSources.length > 0 && (
                          <SourceSummary sources={streamingSources} className="mt-3" />
                        )}
                        {onAbortStream && (
                          <div className="mt-3 flex justify-start">
                            <button
                              onClick={onAbortStream}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-foreground bg-background border border-border rounded-full hover:bg-muted-foreground/10 transition-colors"
                            >
                              <Square className="w-3 h-3 fill-current" />
                              Stop generating
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3 p-4 bg-muted rounded-2xl">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                      </div>
                      <div className="space-y-2 flex-1">
                        <div className="h-3 bg-muted-foreground/20 rounded animate-pulse" />
                        <div className="h-3 bg-muted-foreground/20 rounded animate-pulse w-3/4" />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}

        {/* Global Loading State */}
        {isLoading && messages.length === 0 && (
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-3 text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>AmaniQuery is thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

interface StreamingMessageProps {
  content: string
  isThinking?: boolean
  sources?: any[]
  className?: string
}

export function StreamingMessage({ 
  content, 
  isThinking = false, 
  sources = [],
  className 
}: StreamingMessageProps) {
  return (
    <div className={cn("ml-12 space-y-3", className)}>
      {isThinking && (
        <CompactThinkingIndicator isActive={true} />
      )}
      <div className="flex items-start gap-3 p-4 bg-muted rounded-2xl animate-in fade-in duration-300">
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
          <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {content ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ children }) => <span className="block mb-2 leading-7">{children}</span>,
                  code: ({ children, className }) => {
                    const match = /language-(\w+)/.exec(className || "")
                    const isInline = !match && !String(children).includes("\n")
                    return isInline ? (
                      <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono">{children}</code>
                    ) : (
                      <div className="my-2 rounded border border-border bg-muted/50 p-3 overflow-x-auto">
                        <code className="text-sm font-mono">{children}</code>
                      </div>
                    )
                  },
                }}
              >
                {content}
              </ReactMarkdown>
            ) : (
              <span className="text-muted-foreground">Thinking...</span>
            )}
          </div>
          {sources.length > 0 && (
            <SourceSummary sources={sources} className="mt-3" />
          )}
        </div>
      </div>
    </div>
  )
}