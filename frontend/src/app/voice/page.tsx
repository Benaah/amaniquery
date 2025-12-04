"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { VoiceAgentWrapper } from "@/components/voice-agent-wrapper"
import { ThemeToggle } from "@/components/theme-toggle"
import { Sidebar } from "@/components/sidebar"
import { useAuth } from "@/lib/auth-context"

export default function VoicePage() {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/signin?redirect=/voice")
    }
  }, [isAuthenticated, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black text-cyan-500">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar />
      <div className="flex-1 ml-0 md:ml-[20px] flex flex-col h-screen overflow-hidden relative selection:bg-cyan-500/30">
        
        {/* Background Elements */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/10 via-background to-background pointer-events-none" />
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-30 dark:opacity-50" />
        
        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(100,100,100,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(100,100,100,0.05)_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />

        <div className="relative z-10 flex-1 flex flex-col min-h-0">
          {/* Header */}
          <header className="h-16 border-b border-border/40 bg-background/50 backdrop-blur-md flex items-center justify-between px-6 flex-shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                <span className="font-bold text-white text-lg">A</span>
              </div>
              <h1 className="text-xl font-bold tracking-wider text-foreground">
                Amani<span className="text-cyan-500">Q</span>
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <ThemeToggle />
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1 p-4 md:p-6 overflow-hidden flex flex-col">
            <VoiceAgentWrapper />
          </main>
        </div>
      </div>
    </div>
  )
}
