"use client"

import { useState, useEffect, useRef } from "react"
import { Room, RoomEvent, Track, RemoteParticipant } from "livekit-client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Mic, MicOff, Volume2, VolumeX, Loader2 } from "lucide-react"

interface VoiceAgentProps {
  livekitUrl: string
  token: string
  roomName: string
}

export function VoiceAgent({ livekitUrl, token, roomName }: VoiceAgentProps) {
  const [room, setRoom] = useState<Room | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const roomRef = useRef<Room | null>(null)

  useEffect(() => {
    const connect = async () => {
      // Validate URL before attempting connection
      if (!livekitUrl || livekitUrl.trim() === "") {
        setError("LiveKit URL is not configured")
        return
      }

      // Validate URL format
      try {
        new URL(livekitUrl)
      } catch {
        setError(`Invalid LiveKit URL format: ${livekitUrl}. URL must be a valid WebSocket URL (ws:// or wss://)`)
        return
      }

      if (!token || token.trim() === "") {
        setError("Token is missing")
        return
      }

      // Check if media devices are available (required for microphone access)
      if (typeof window !== "undefined" && !navigator.mediaDevices?.getUserMedia) {
        const isSecure = window.location.protocol === "https:" || window.location.hostname === "localhost"
        if (!isSecure) {
          setError("Microphone access requires HTTPS. Please access this page over HTTPS or use localhost.")
          return
        } else {
          setError("Your browser doesn't support microphone access. Please use a modern browser like Chrome, Firefox, or Edge.")
          return
        }
      }

      try {
        const newRoom = new Room()
        roomRef.current = newRoom
        
        newRoom.on(RoomEvent.Connected, () => {
          setIsConnected(true)
          setError(null)
        })

        newRoom.on(RoomEvent.Disconnected, () => {
          setIsConnected(false)
        })

        newRoom.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
          if (track.kind === Track.Kind.Audio && participant instanceof RemoteParticipant) {
            const audioElement = audioRef.current
            if (audioElement) {
              track.attach(audioElement)
              audioElement.play().catch(console.error)
            }
          }
        })

        newRoom.on(RoomEvent.TrackUnsubscribed, (track) => {
          track.detach()
        })

        newRoom.on(RoomEvent.ParticipantConnected, (participant) => {
          if (participant instanceof RemoteParticipant) {
            setIsSpeaking(true)
          }
        })

        newRoom.on(RoomEvent.ParticipantDisconnected, () => {
          setIsSpeaking(false)
        })

        await newRoom.connect(livekitUrl, token)
        
        // Enable only microphone (not camera) for voice-only agent
        // Request microphone permission explicitly
        try {
          if (navigator.mediaDevices?.getUserMedia) {
            // Request permission first
            await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
          }
          await newRoom.localParticipant.setMicrophoneEnabled(true)
        } catch (mediaError) {
          if (mediaError instanceof Error) {
            if (mediaError.name === "NotAllowedError" || mediaError.name === "PermissionDeniedError") {
              setError("Microphone permission denied. Please allow microphone access and try again.")
            } else if (mediaError.name === "NotFoundError" || mediaError.name === "DevicesNotFoundError") {
              setError("No microphone found. Please connect a microphone and try again.")
            } else {
              setError(`Microphone error: ${mediaError.message}`)
            }
          } else {
            setError("Failed to access microphone. Please check your browser permissions.")
          }
          await newRoom.disconnect()
          roomRef.current = null
          return
        }
        
        setRoom(newRoom)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to connect")
        setIsConnected(false)
        roomRef.current = null
      }
    }

    connect()

    return () => {
      if (roomRef.current) {
        roomRef.current.disconnect()
        roomRef.current = null
      }
    }
  }, [livekitUrl, token])

  const toggleMute = async () => {
    if (!room) return
    
    if (isMuted) {
      await room.localParticipant.setMicrophoneEnabled(true)
      setIsMuted(false)
    } else {
      await room.localParticipant.setMicrophoneEnabled(false)
      setIsMuted(true)
    }
  }

  const disconnect = async () => {
    if (room) {
      await room.disconnect()
      setIsConnected(false)
    }
  }

  if (error) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardContent className="pt-6">
          <p className="text-destructive text-sm">{error}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Volume2 className="w-5 h-5" />
          Voice Assistant
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${
                isConnected ? "bg-green-500 animate-pulse" : "bg-gray-400"
              }`}
            />
            <span className="text-sm">
              {isConnected ? "Connected" : "Connecting..."}
            </span>
          </div>
          {isSpeaking && (
            <div className="flex items-center gap-1 text-sm text-primary">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Agent speaking...</span>
            </div>
          )}
        </div>

        <audio ref={audioRef} autoPlay />

        <div className="flex gap-2">
          <Button
            onClick={toggleMute}
            variant={isMuted ? "destructive" : "default"}
            className="flex-1"
            disabled={!isConnected}
          >
            {isMuted ? (
              <>
                <MicOff className="w-4 h-4 mr-2" />
                Unmute
              </>
            ) : (
              <>
                <Mic className="w-4 h-4 mr-2" />
                Mute
              </>
            )}
          </Button>

          <Button
            onClick={disconnect}
            variant="outline"
            disabled={!isConnected}
          >
            Disconnect
          </Button>
        </div>

        <p className="text-xs text-muted-foreground text-center">
          Room: {roomName}
        </p>
      </CardContent>
    </Card>
  )
}

