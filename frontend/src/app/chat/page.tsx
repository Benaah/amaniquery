import { Chat } from "@/components/chat"
import { ThemeToggle } from "@/components/theme-toggle"

export default function ChatPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <Chat />
    </div>
  )
}