"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { VoiceChat } from "@/components/voice-chat"
import { AmaniSidebar } from "@/components/AmaniSidebar"
import { useAuth } from "@/lib/auth-context"
import { Mic, ChevronRight } from "lucide-react"
import type { ChatSession } from "@/components/chat/types"

export default function VoicePage() {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()
  
  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [chatHistory] = useState<ChatSession[]>([])

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/signin?redirect=/voice")
    }
  }, [isAuthenticated, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  // No-op handlers for sidebar
  const handleSessionSelect = () => {}
  const handleNewSession = () => router.push("/chat")
  const handleDeleteSession = () => {}
  const handleRenameSession = () => {}

  return (
    <div className="min-h-screen bg-background flex">
      <AmaniSidebar
        chatHistory={chatHistory}
        currentSessionId={null}
        onSessionSelect={handleSessionSelect}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        onRenameSession={handleRenameSession}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      
      <div className="flex-1 flex flex-col h-screen overflow-hidden relative">
        <div className="relative z-10 flex-1 flex flex-col min-h-0">
          {/* Header */}
          <header className="h-14 border-b border-border bg-background flex items-center justify-between px-4 flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>AmaniQuery</span>
                <ChevronRight className="w-4 h-4" />
                <span className="text-foreground font-medium flex items-center gap-2">
                  <Mic className="w-4 h-4" />
                  Voice Mode
                </span>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1 p-0 overflow-hidden flex flex-col">
            <VoiceChat />
          </main>
        </div>
      </div>
    </div>
  )
}
