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

  useEffect(() => {
    const connect = async () => {
      try {
        const newRoom = new Room()
        
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
        await newRoom.localParticipant.enableCameraAndMicrophone()
        setRoom(newRoom)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to connect")
        setIsConnected(false)
      }
    }

    connect()

    return () => {
      if (room) {
        room.disconnect()
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

