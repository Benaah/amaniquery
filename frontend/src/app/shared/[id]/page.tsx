"use client"

import { useEffect, useState, useRef } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { MessageList } from "@/components/chat/MessageList"
import { Message } from "@/components/chat/types"
import { Loader2 } from "lucide-react"
import { toast } from "sonner"

export default function SharedChatPage() {
  const params = useParams()
  const id = params.id as string
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [title, setTitle] = useState<string>("")
  const [showSources, setShowSources] = useState(false)
  
  // Refs for auto-scrolling
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const fetchSharedSession = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/chat/shared/${id}`)
        if (!response.ok) {
          throw new Error("Failed to load shared chat")
        }
        const data = await response.json()
        setMessages(data.messages)
        setTitle(data.title)
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred")
      } finally {
        setIsLoading(false)
      }
    }

    if (id) {
      fetchSharedSession()
    }
  }, [id])

  // No-op handlers for read-only view
  const noOp = () => {}

  const handleCopy = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      toast.success("Copied to clipboard")
    } catch {
      toast.error("Failed to copy")
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background text-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-background text-foreground">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-500">Error</h1>
          <p className="mt-2 text-muted-foreground">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen flex-col bg-gradient-to-b from-background via-background/95 to-background text-foreground overflow-hidden">
      <div className="pointer-events-none absolute inset-0 opacity-60">
        <div className="absolute -top-32 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-primary/20 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-blue-500/10 blur-[120px]" />
      </div>

      <header className="relative z-10 border-b border-white/10 bg-black/20 backdrop-blur-xl px-6 py-4">
        <div className="mx-auto max-w-3xl flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">{title || "Shared Chat"}</h1>
            <p className="text-xs text-muted-foreground">Shared via AmaniQuery</p>
          </div>
          <Link href="/" className="text-sm font-medium text-primary hover:underline">
            Start your own chat
          </Link>
        </div>
      </header>
      
      <div className="flex-1 flex flex-col relative z-10 h-full overflow-hidden min-w-0">
         <div className="flex-1 flex flex-col max-w-5xl mx-auto w-full">
            <MessageList
              messages={messages}
              isLoading={false}
              isResearchMode={false}
              useHybrid={false}
              onSendMessage={noOp}
              onRegenerate={noOp}
              onFeedback={noOp}
              onCopy={handleCopy}
              onShare={noOp}
              onGeneratePDF={noOp}
              onGenerateWord={noOp}
              showSources={showSources}
              onToggleSources={() => setShowSources(!showSources)}
              messagesContainerRef={messagesContainerRef}
              messagesEndRef={messagesEndRef}
              editingMessageId={null}
              editingContent=""
              setEditingContent={noOp}
              onSaveEdit={noOp}
              onCancelEdit={noOp}
              onStartEdit={noOp}
              regeneratingMessageId={null}
              shareSheet={null}
              onCloseShareSheet={noOp}
              onChangeSharePlatform={noOp}
              onCopyShareContent={noOp}
              onOpenShareIntent={noOp}
              onPostDirectly={noOp}
              onCopyFailedQuery={noOp}
              onEditFailedQuery={noOp}
              onResendFailedQuery={noOp}
            />
         </div>
      </div>
    </div>
  )
}
