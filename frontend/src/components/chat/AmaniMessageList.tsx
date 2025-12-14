"use client"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { AmaniMessage } from "./AmaniMessage"
import { MessageActions } from "./MessageActions"
import { ThinkingIndicator, CompactThinkingIndicator } from "./ThinkingIndicator"
import { SourcePanel, SourceSummary } from "./SourcePanel"
import { WelcomeScreen } from "./WelcomeScreen"
import { Loader2 } from "lucide-react"
import type { Message } from "./types"

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
  messageClassName
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
        <WelcomeScreen onSendMessage={onSendMessage} />
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
                  />
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
                </div>
              )}

              {/* Loading State for Current Response */}
              {!group.hasAssistantResponse && isLoading && group === messageGroups[messageGroups.length - 1] && (
                <div className="ml-12 space-y-3 animate-in fade-in duration-500">
                  {enableThinkingIndicator && (
                    <ThinkingIndicator
                      isActive={true}
                      defaultExpanded={false}
                      className="mb-3"
                    />
                  )}
                  <div className="flex items-center gap-3 p-4 bg-muted rounded-2xl">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                    <div className="space-y-2 flex-1">
                      <div className="h-3 bg-muted-foreground/20 rounded animate-pulse" />
                      <div className="h-3 bg-muted-foreground/20 rounded animate-pulse w-3/4" />
                    </div>
                  </div>
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
          <div className="prose prose-sm max-w-none">
            <div 
              className="whitespace-pre-wrap"
              dangerouslySetInnerHTML={{ 
                __html: content || '<span class="text-muted-foreground">Thinking...</span>' 
              }}
            />
          </div>
          {sources.length > 0 && (
            <SourceSummary sources={sources} className="mt-3" />
          )}
        </div>
      </div>
    </div>
  )
}