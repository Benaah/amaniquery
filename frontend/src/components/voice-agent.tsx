"use client"

import { useState, useEffect, useRef } from "react"
import { Room, RoomEvent, Track, RemoteParticipant, DataPacket_Kind } from "livekit-client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Mic, MicOff, Volume2, Loader2 } from "lucide-react"
import { TranscriptDisplay, TranscriptMessage } from "./transcript-display"
import { AudioWaveform } from "./audio-waveform"
import { OpenAIVoice } from "./voice-selector"

interface VoiceAgentProps {
  livekitUrl: string
  token: string
  roomName: string
  selectedVoice?: OpenAIVoice
}

export function VoiceAgent({ livekitUrl, token, roomName, selectedVoice = "alloy" }: VoiceAgentProps) {
  const [room, setRoom] = useState<Room | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [messages, setMessages] = useState<TranscriptMessage[]>([])
  const [currentUserTranscript, setCurrentUserTranscript] = useState("")
  const [currentAgentTranscript, setCurrentAgentTranscript] = useState("")
  const [isUserTranscribing, setIsUserTranscribing] = useState(false)
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null)
  
  // Type definitions for Web Speech API
  interface SpeechRecognition extends EventTarget {
    continuous: boolean
    interimResults: boolean
    lang: string
    start: () => void
    stop: () => void
    onstart: ((this: SpeechRecognition, ev: Event) => void) | null
    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null
    onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null
    onend: (() => void) | null
  }

  interface SpeechRecognitionEvent extends Event {
    resultIndex: number
    results: SpeechRecognitionResultList
  }

  interface SpeechRecognitionResultList {
    length: number
    item(index: number): SpeechRecognitionResult
    [index: number]: SpeechRecognitionResult
  }

  interface SpeechRecognitionResult {
    length: number
    item(index: number): SpeechRecognitionAlternative
    [index: number]: SpeechRecognitionAlternative
    isFinal: boolean
  }

  interface SpeechRecognitionAlternative {
    transcript: string
    confidence: number
  }

  interface SpeechRecognitionErrorEvent extends Event {
    error: string
  }

  interface SpeechRecognitionConstructor {
    new (): SpeechRecognition
  }

  const audioRef = useRef<HTMLAudioElement>(null)
  const roomRef = useRef<Room | null>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const userTranscriptIdRef = useRef<string | null>(null)
  const agentTranscriptIdRef = useRef<string | null>(null)

  // Fallback TTS using Web Speech API (for offline/TTS failures)
  const speakWithBrowserTTS = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = "sw-KE" // Swahili (Kenya)
      // Fallback to English if Swahili not available
      const voices = speechSynthesis.getVoices()
      const swahiliVoice = voices.find(v => v.lang.startsWith('sw'))
      if (swahiliVoice) {
        utterance.voice = swahiliVoice
      }
      speechSynthesis.speak(utterance)
    }
  }

  // Initialize Web Speech API for user transcription
  useEffect(() => {
    if (typeof window === "undefined") return

    const SpeechRecognition = ((window as unknown as { SpeechRecognition?: SpeechRecognitionConstructor }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: SpeechRecognitionConstructor }).webkitSpeechRecognition) as SpeechRecognitionConstructor | undefined
    if (!SpeechRecognition) {
      console.warn("Web Speech API not supported in this browser")
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = "en-US"

    recognition.onstart = () => {
      setIsUserTranscribing(true)
    }

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interimTranscript = ""
      let finalTranscript = ""

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript + " "
        } else {
          interimTranscript += transcript
        }
      }

      if (finalTranscript) {
        // Final transcript - add to messages
        if (userTranscriptIdRef.current) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === userTranscriptIdRef.current
                ? { ...msg, content: msg.content + finalTranscript.trim(), isStreaming: false }
                : msg
            )
          )
          userTranscriptIdRef.current = null
        } else {
          const newMessage: TranscriptMessage = {
            id: `user-${Date.now()}`,
            role: "user",
            content: finalTranscript.trim(),
            timestamp: new Date(),
            isStreaming: false,
          }
          setMessages((prev) => [...prev, newMessage])
        }
        setCurrentUserTranscript("")
      } else if (interimTranscript) {
        // Interim transcript - update streaming message
        setCurrentUserTranscript(interimTranscript)
        if (!userTranscriptIdRef.current) {
          const newMessage: TranscriptMessage = {
            id: `user-${Date.now()}`,
            role: "user",
            content: interimTranscript,
            timestamp: new Date(),
            isStreaming: true,
          }
          userTranscriptIdRef.current = newMessage.id
          setMessages((prev) => [...prev, newMessage])
        } else {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === userTranscriptIdRef.current
                ? { ...msg, content: interimTranscript, isStreaming: true }
                : msg
            )
          )
        }
      }
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      // Ignore common, non-critical errors
      if (["no-speech", "audio-capture", "network", "aborted"].includes(event.error)) {
        // These are common and can be ignored - network errors are often temporary
        return
      }
      // Only log unexpected errors
      console.warn("Speech recognition error:", event.error)
    }

    recognition.onend = () => {
      setIsUserTranscribing(false)
      // Restart recognition if connected and not muted
      if (isConnected && !isMuted && room) {
        try {
          recognition.start()
        } catch {
          // Recognition might already be starting
        }
      }
    }

    recognitionRef.current = recognition

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch {
          // Ignore errors on cleanup
        }
      }
    }
  }, [isConnected, isMuted, room])

  // Start/stop recognition based on connection and mute state
  useEffect(() => {
    if (!recognitionRef.current) return

    if (isConnected && !isMuted) {
      try {
        recognitionRef.current.start()
      } catch {
        // Recognition might already be running
      }
    } else {
      try {
        recognitionRef.current.stop()
      } catch {
        // Ignore errors
      }
    }
  }, [isConnected, isMuted])

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

        // Listen for data messages (agent transcriptions)
        newRoom.on(RoomEvent.DataReceived, (payload, participant, kind) => {
          if (kind === DataPacket_Kind.RELIABLE && participant instanceof RemoteParticipant) {
            try {
              const data = JSON.parse(new TextDecoder().decode(payload))
              if (data.type === "transcription" && data.role === "agent") {
                const transcript = data.text || ""
                
                // Handle TTS failure - use browser fallback
                if (data.tts_failed && transcript) {
                  speakWithBrowserTTS(transcript)
                }
                
                if (data.isFinal) {
                  // Final transcript
                  if (agentTranscriptIdRef.current) {
                    setMessages((prev) =>
                      prev.map((msg) =>
                        msg.id === agentTranscriptIdRef.current
                          ? { ...msg, content: msg.content + transcript, isStreaming: false }
                          : msg
                      )
                    )
                    agentTranscriptIdRef.current = null
                  } else {
                    const newMessage: TranscriptMessage = {
                      id: `agent-${Date.now()}`,
                      role: "agent",
                      content: transcript,
                      timestamp: new Date(),
                      isStreaming: false,
                    }
                    setMessages((prev) => [...prev, newMessage])
                  }
                  setCurrentAgentTranscript("")
                } else {
                  // Interim transcript
                  setCurrentAgentTranscript(transcript)
                  if (!agentTranscriptIdRef.current) {
                    const newMessage: TranscriptMessage = {
                      id: `agent-${Date.now()}`,
                      role: "agent",
                      content: transcript,
                      timestamp: new Date(),
                      isStreaming: true,
                    }
                    agentTranscriptIdRef.current = newMessage.id
                    setMessages((prev) => [...prev, newMessage])
                  } else {
                    setMessages((prev) =>
                      prev.map((msg) =>
                        msg.id === agentTranscriptIdRef.current
                          ? { ...msg, content: transcript, isStreaming: true }
                          : msg
                      )
                    )
                  }
                }
              }
            } catch {
              // Ignore non-JSON data or parsing errors
            }
          }
        })

        await newRoom.connect(livekitUrl, token)

        // Send voice selection to agent via data channel
        if (selectedVoice) {
          try {
            const data = JSON.stringify({ type: "voice_selection", voice: selectedVoice })
            await newRoom.localParticipant.publishData(
              new TextEncoder().encode(data),
              { reliable: true }
            )
          } catch {
            console.warn("Failed to send voice selection")
          }
        }

        // Enable only microphone (not camera) for voice-only agent
        // Request microphone permission explicitly
        try {
          if (navigator.mediaDevices?.getUserMedia) {
            // Request permission first and get stream for waveform
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
            setAudioStream(stream)
            
            // Also enable in LiveKit
            await newRoom.localParticipant.setMicrophoneEnabled(true)
          }
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
      // Cleanup audio stream
      setAudioStream((currentStream) => {
        if (currentStream) {
          currentStream.getTracks().forEach((track) => track.stop())
        }
        return null
      })
    }
  }, [livekitUrl, token, selectedVoice])

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
    if (audioStream) {
      audioStream.getTracks().forEach((track) => track.stop())
      setAudioStream(null)
    }
    setMessages([])
    setCurrentUserTranscript("")
    setCurrentAgentTranscript("")
  }

  // Update messages with current streaming transcripts
  const displayMessages = messages.map((msg) => {
    if (msg.isStreaming) {
      if (msg.role === "user" && currentUserTranscript) {
        return { ...msg, content: currentUserTranscript }
      }
      if (msg.role === "agent" && currentAgentTranscript) {
        return { ...msg, content: currentAgentTranscript }
      }
    }
    return msg
  })

  if (error) {
    return (
      <Card className="w-full">
        <CardContent className="pt-6">
          <p className="text-destructive text-sm">{error}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Transcript Display */}
      <Card className="flex-1 flex flex-col min-h-0">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Volume2 className="w-5 h-5" />
            Conversation
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 min-h-0 p-0">
          <TranscriptDisplay messages={displayMessages} className="h-full" />
        </CardContent>
      </Card>

      {/* Waveform Visualization */}
      <AudioWaveform
        audioStream={audioStream}
        isActive={isConnected && !isMuted && (isUserTranscribing || isSpeaking)}
      />

      {/* Controls */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
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
              {isUserTranscribing && (
                <div className="flex items-center gap-1 text-sm text-primary">
                  <Mic className={`w-4 h-4 ${isUserTranscribing ? "animate-pulse" : ""}`} />
                  <span>Listening...</span>
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
              Room: {roomName} | Voice: {selectedVoice}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
