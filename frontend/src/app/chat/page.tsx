"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { Chat } from "@/components/chat"
import { ThemeToggle } from "@/components/theme-toggle"
import { Sidebar } from "@/components/sidebar"
import { useAuth } from "@/lib/auth-context"

export default function ChatPage() {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()

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
      <Sidebar />
      <div className="flex-1 ml-0 md:ml-[20px] min-w-0 overflow-hidden relative">
        <div className="absolute top-2 right-2 md:top-4 md:right-4 z-10">
          <ThemeToggle />
        </div>
        <Chat />
      </div>
    </div>
  )
}