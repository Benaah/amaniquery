"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { AmaniChat } from "@/components/chat/AmaniChat"
import { AmaniSidebar } from "@/components/AmaniSidebar"
import { ThemeToggle } from "@/components/theme-toggle"
import { useAuth } from "@/lib/auth-context"
import { cn } from "@/lib/utils"
import type { ChatSession } from "@/components/chat/types"

export default function ChatPage() {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()
  const [chatHistory, setChatHistory] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  // Load chat history on mount
  useEffect(() => {
    if (isAuthenticated) {
      loadChatHistory()
    }
  }, [isAuthenticated])

  const loadChatHistory = async () => {
    try {
      const token = localStorage.getItem("session_token")
      const headers = { "X-Session-Token": token || "" }
      const response = await fetch("/api/cache/sessions", { headers })
      if (response.ok) {
        const sessions = await response.json()
        setChatHistory(sessions)
      }
    } catch (error) {
      console.error("Failed to load chat history:", error)
    }
  }

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/signin?redirect=/chat")
    }
  }, [isAuthenticated, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen max-h-screen bg-background flex overflow-hidden">
      {/* New AmaniSidebar with integrated chat history */}
      <AmaniSidebar
        chatHistory={chatHistory}
        currentSessionId={currentSessionId}
        onSessionSelect={setCurrentSessionId}
        onNewSession={() => setCurrentSessionId(null)}
        onDeleteSession={async (sessionId) => {
          // Handle session deletion
          setChatHistory(prev => prev.filter(s => s.id !== sessionId))
          if (currentSessionId === sessionId) {
            setCurrentSessionId(null)
          }
          // Call API to delete session
          try {
            const token = localStorage.getItem("session_token")
            const headers = { "X-Session-Token": token || "" }
            await fetch(`/api/v1/chat/sessions/${sessionId}`, {
              method: "DELETE",
              headers
            })
          } catch (error) {
            console.error("Failed to delete session:", error)
          }
        }}
        onRenameSession={async (sessionId, newTitle) => {
          // Handle session renaming
          setChatHistory(prev => prev.map(s => 
            s.id === sessionId ? { ...s, title: newTitle } : s
          ))
          // Call API to rename session
          try {
            const token = localStorage.getItem("session_token")
            const headers = { 
              "X-Session-Token": token || "",
              "Content-Type": "application/json"
            }
            await fetch(`/api/v1/chat/sessions/${sessionId}`, {
              method: "PATCH",
              headers,
              body: JSON.stringify({ title: newTitle })
            })
          } catch (error) {
            console.error("Failed to rename session:", error)
          }
        }}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />
      
      {/* Main Chat Area */}
      <div className={cn(
        "flex-1 min-w-0 overflow-hidden relative transition-all duration-300",
        isSidebarOpen ? "md:ml-0" : "md:ml-0"
      )}>
        <div className="absolute top-2 right-2 md:top-4 md:right-4 z-10">
          <ThemeToggle />
        </div>
        <AmaniChat 
          showWelcomeScreen={true}
          enableThinkingIndicator={true}
          showInlineSources={true}
          enableVoice={false}
          currentSessionId={currentSessionId}
          onSessionChange={setCurrentSessionId}
          chatHistory={chatHistory}
          onChatHistoryUpdate={setChatHistory}
        />
      </div>
    </div>
  )
}