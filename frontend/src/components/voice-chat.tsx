"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Mic, MicOff, Volume2, Loader2, StopCircle } from "lucide-react"

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

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  audioUrl?: string
}

interface VoiceInfo {
  name: string
  language: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ""

export function VoiceChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentTranscript, setCurrentTranscript] = useState("")
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [voices, setVoices] = useState<VoiceInfo[]>([])
  const [selectedVoice, setSelectedVoice] = useState("Wayne")
  const [speechSupported, setSpeechSupported] = useState(true)

  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Fetch available voices
  useEffect(() => {
    const fetchVoices = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/voice/voices`)
        if (response.ok) {
          const data = await response.json()
          setVoices(data)
          if (data.length > 0) {
            setSelectedVoice(data[0].name)
          }
        }
      } catch (e) {
        console.warn("Failed to fetch voices:", e)
      }
    }
    fetchVoices()
  }, [])

  // Initialize Web Speech API
  useEffect(() => {
    if (typeof window === "undefined") return

    const SpeechRecognition = ((window as unknown as { SpeechRecognition?: SpeechRecognitionConstructor }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: SpeechRecognitionConstructor }).webkitSpeechRecognition) as SpeechRecognitionConstructor | undefined

    if (!SpeechRecognition) {
      setSpeechSupported(false)
      setError("Speech recognition not supported in this browser. Please use Chrome, Edge, or Safari.")
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = "en-US"

    recognition.onstart = () => {
      setIsListening(true)
      setError(null)
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
        // Final transcript - send to API
        setCurrentTranscript("")
        handleUserQuery(finalTranscript.trim())
      } else if (interimTranscript) {
        setCurrentTranscript(interimTranscript)
      }
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (!["no-speech", "aborted"].includes(event.error)) {
        console.warn("Speech recognition error:", event.error)
        if (event.error === "not-allowed") {
          setError("Microphone permission denied. Please allow microphone access.")
        }
      }
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognitionRef.current = recognition

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch {}
      }
    }
  }, [])

  const handleUserQuery = useCallback(async (text: string) => {
    if (!text.trim() || isProcessing) return

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])

    // Stop listening while processing
    try {
      recognitionRef.current?.stop()
    } catch {}

    setIsProcessing(true)
    setError(null)

    try {
      // Call voice chat API
      const response = await fetch(`${API_BASE}/api/v1/voice/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          voice: selectedVoice,
          category: "Kenyan Law",
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || "Failed to get response")
      }

      const data = await response.json()

      // Add assistant message
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.answer,
        timestamp: new Date(),
        audioUrl: `${API_BASE}${data.audio_url}`,
      }
      setMessages(prev => [...prev, assistantMessage])

      // Play audio
      if (data.audio_url) {
        playAudio(`${API_BASE}${data.audio_url}`)
      }

    } catch (e) {
      console.error("Voice chat error:", e)
      setError(e instanceof Error ? e.message : "Failed to process query")
    } finally {
      setIsProcessing(false)
    }
  }, [selectedVoice, isProcessing])

  const playAudio = (url: string) => {
    if (audioRef.current) {
      audioRef.current.src = url
      audioRef.current.play()
        .then(() => setIsPlaying(true))
        .catch(console.error)
    }
  }

  const handleAudioEnded = () => {
    setIsPlaying(false)
  }

  const toggleListening = () => {
    if (!speechSupported) return

    if (isListening) {
      recognitionRef.current?.stop()
    } else {
      setCurrentTranscript("")
      try {
        recognitionRef.current?.start()
      } catch (e) {
        console.error("Failed to start recognition:", e)
      }
    }
  }

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      setIsPlaying(false)
    }
  }

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto gap-4">
      {/* Hidden audio element */}
      <audio ref={audioRef} onEnded={handleAudioEnded} className="hidden" />

      {/* Messages Area */}
      <Card className="flex-1 overflow-hidden flex flex-col bg-background/60 backdrop-blur-sm border-border/40">
        <CardHeader className="border-b border-border/40 py-4">
          <CardTitle className="flex items-center gap-3 text-lg">
            <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500/20 to-cyan-500/20 border border-purple-500/20">
              <Volume2 className="w-5 h-5 text-purple-500" />
            </div>
            <span>AmaniQuery Voice</span>
            {voices.length > 0 && (
              <select
                value={selectedVoice}
                onChange={(e) => setSelectedVoice(e.target.value)}
                className="ml-auto text-sm bg-muted border border-border rounded px-2 py-1"
              >
                {voices.map(v => (
                  <option key={v.name} value={v.name}>{v.name}</option>
                ))}
              </select>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground text-center">
              <Volume2 className="w-12 h-12 mb-4 opacity-50" />
              <p className="text-lg font-medium">Voice Assistant</p>
              <p className="text-sm mt-2">Click the microphone and ask about Kenyan law, parliament, or news.</p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] p-3 rounded-2xl ${
                  msg.role === "user"
                    ? "bg-cyan-600/20 border border-cyan-500/30 rounded-tr-none"
                    : "bg-purple-600/20 border border-purple-500/30 rounded-tl-none"
                }`}
              >
                <p className="text-sm">{msg.content}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {msg.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}

          {/* Current transcript (interim) */}
          {currentTranscript && (
            <div className="flex justify-end">
              <div className="max-w-[80%] p-3 rounded-2xl bg-cyan-600/10 border border-cyan-500/20 rounded-tr-none animate-pulse">
                <p className="text-sm text-cyan-400/70 italic">{currentTranscript}</p>
              </div>
            </div>
          )}

          {/* Processing indicator */}
          {isProcessing && (
            <div className="flex justify-start">
              <div className="p-3 rounded-2xl bg-purple-600/10 border border-purple-500/20 rounded-tl-none">
                <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>
      </Card>

      {/* Error display */}
      {error && (
        <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive text-sm">
          {error}
        </div>
      )}

      {/* Controls */}
      <Card className="bg-background/60 backdrop-blur-sm border-border/40">
        <CardContent className="p-4 flex items-center justify-center gap-4">
          {/* Mic button */}
          <Button
            onClick={toggleListening}
            disabled={!speechSupported || isProcessing}
            size="lg"
            className={`w-16 h-16 rounded-full ${
              isListening
                ? "bg-red-500 hover:bg-red-600 animate-pulse"
                : "bg-gradient-to-br from-cyan-500 to-purple-600 hover:opacity-90"
            }`}
          >
            {isListening ? (
              <MicOff className="w-6 h-6" />
            ) : (
              <Mic className="w-6 h-6" />
            )}
          </Button>

          {/* Stop audio button */}
          {isPlaying && (
            <Button
              onClick={stopAudio}
              variant="outline"
              size="lg"
              className="w-16 h-16 rounded-full border-orange-500/50 text-orange-500 hover:bg-orange-500/10"
            >
              <StopCircle className="w-6 h-6" />
            </Button>
          )}

          {/* Status text */}
          <div className="text-sm text-muted-foreground">
            {isProcessing ? (
              "Processing..."
            ) : isListening ? (
              <span className="text-cyan-500">Listening...</span>
            ) : isPlaying ? (
              <span className="text-purple-500">Playing response...</span>
            ) : (
              "Click mic to speak"
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
