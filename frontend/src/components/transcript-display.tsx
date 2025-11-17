"use client"

import { useEffect, useRef } from "react"
import { cn } from "@/lib/utils"
import { User, Bot } from "lucide-react"

export interface TranscriptMessage {
  id: string
  role: "user" | "agent"
  content: string
  timestamp: Date
  isStreaming?: boolean
}

interface TranscriptDisplayProps {
  messages: TranscriptMessage[]
  className?: string
}

export function TranscriptDisplay({ messages, className }: TranscriptDisplayProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(date)
  }

  return (
    <div
      ref={scrollRef}
      className={cn(
        "flex flex-col gap-4 h-full overflow-y-auto p-4",
        "scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent",
        className
      )}
    >
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
          <div className="text-center">
            <p>Start speaking to see the conversation transcript</p>
            <p className="text-xs mt-2">Your words will appear here in real-time</p>
          </div>
        </div>
      ) : (
        messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex gap-3 animate-in fade-in slide-in-from-bottom-2",
              message.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            {message.role === "agent" && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="w-4 h-4 text-primary" />
              </div>
            )}
            
            <div
              className={cn(
                "max-w-[80%] rounded-2xl px-4 py-3 shadow-sm",
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground"
              )}
            >
              <div className="flex items-start gap-2">
                <div className="flex-1">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                    {message.content}
                    {message.isStreaming && (
                      <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
                    )}
                  </p>
                </div>
              </div>
              <div
                className={cn(
                  "text-xs mt-2 opacity-70",
                  message.role === "user" ? "text-primary-foreground/70" : "text-muted-foreground/70"
                )}
              >
                {formatTime(message.timestamp)}
              </div>
            </div>

            {message.role === "user" && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="w-4 h-4 text-primary" />
              </div>
            )}
          </div>
        ))
      )}
    </div>
  )
}

