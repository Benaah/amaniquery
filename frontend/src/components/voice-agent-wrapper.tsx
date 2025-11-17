"use client"

import { useState } from "react"
import { VoiceAgent } from "./voice-agent"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { VoiceSelector, OpenAIVoice } from "./voice-selector"

export function VoiceAgentWrapper() {
  const [roomName, setRoomName] = useState(`voice-${Date.now()}`)
  const [token, setToken] = useState<string | null>(null)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedVoice, setSelectedVoice] = useState<OpenAIVoice>("alloy")

  const livekitUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || ""

  const generateToken = async () => {
    if (!livekitUrl || livekitUrl.trim() === "") {
      setError("LiveKit URL is not configured. Please set NEXT_PUBLIC_LIVEKIT_URL environment variable.")
      return
    }

    // Validate URL format
    try {
      new URL(livekitUrl)
    } catch {
      setError(`Invalid LiveKit URL format: ${livekitUrl}. URL must start with ws:// or wss://`)
      return
    }

    if (!roomName.trim()) {
      setError("Room name is required")
      return
    }

    setIsConnecting(true)
    setError(null)

    try {
      const response = await fetch("/api/livekit-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          roomName: roomName.trim(),
          participantName: "user",
          voice: selectedVoice, // Pass voice selection to backend
        }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || "Failed to generate token")
      }

      const data = await response.json()
      setToken(data.token)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect")
    } finally {
      setIsConnecting(false)
    }
  }

  if (token) {
    return (
      <VoiceAgent
        livekitUrl={livekitUrl}
        token={token}
        roomName={roomName}
        selectedVoice={selectedVoice}
      />
    )
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Start Voice Session</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm font-medium mb-2 block">Room Name</label>
          <Input
            value={roomName}
            onChange={(e) => setRoomName(e.target.value)}
            placeholder="voice-session"
            disabled={isConnecting}
          />
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">Voice</label>
          <VoiceSelector
            selectedVoice={selectedVoice}
            onVoiceChange={setSelectedVoice}
            disabled={isConnecting}
          />
        </div>

        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        <Button
          onClick={generateToken}
          disabled={isConnecting || !roomName.trim()}
          className="w-full"
        >
          {isConnecting ? "Connecting..." : "Connect"}
        </Button>
      </CardContent>
    </Card>
  )
}
