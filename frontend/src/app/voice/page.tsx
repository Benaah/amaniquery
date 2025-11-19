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
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar />
      <div className="flex-1 ml-0 md:ml-[20px]">
        <div className="absolute top-4 right-4 z-10">
          <ThemeToggle />
        </div>
        <VoiceAgentWrapper />
      </div>
    </div>
  )
}
