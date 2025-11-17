import { VoiceAgentWrapper } from "@/components/voice-agent-wrapper"
import { ThemeToggle } from "@/components/theme-toggle"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"

export default function VoicePage() {
  return (
    <div className="min-h-screen bg-background p-4 md:p-6">
      <div className="absolute top-4 right-4 z-10">
        <ThemeToggle />
      </div>
      <div className="max-w-6xl mx-auto space-y-4">
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="outline" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">Voice Assistant</h1>
            <p className="text-sm text-muted-foreground">
              Ask questions about Kenyan law, parliament, and news using voice
            </p>
          </div>
        </div>
        <div className="h-[calc(100vh-12rem)] min-h-[600px]">
          <VoiceAgentWrapper />
        </div>
      </div>
    </div>
  )
}
