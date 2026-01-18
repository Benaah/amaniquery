"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Mic, MicOff, Volume2, Loader2, StopCircle, User, Bot } from "lucide-react"
import { cn } from "@/lib/utils"

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
  }, [messages, currentTranscript])

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
    // Restart listening if needed (optional)
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
    <div className="flex flex-col h-full max-w-3xl mx-auto w-full relative">
      {/* Hidden audio element */}
      <audio ref={audioRef} onEnded={handleAudioEnded} className="hidden" />

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-secondary flex items-center justify-center">
                 <Mic className="w-8 h-8 text-primary" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">Voice Assistant</h2>
                <p className="text-sm mt-1 max-w-xs mx-auto">Ask questions about Kenyan law, parliament, or current affairs.</p>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                "flex gap-4 animate-in fade-in slide-in-from-bottom-2",
                msg.role === "user" ? "flex-row-reverse" : "flex-row"
              )}
            >
              <div className={cn(
                "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center border",
                msg.role === "user" ? "bg-secondary text-foreground border-transparent" : "bg-primary text-primary-foreground border-transparent"
              )}>
                {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className={cn(
                "flex-1 max-w-[80%]",
                msg.role === "user" ? "text-right" : "text-left"
              )}>
                <div className={cn(
                  "inline-block px-5 py-3 text-base leading-relaxed text-left",
                  msg.role === "user" 
                    ? "bg-secondary text-secondary-foreground rounded-3xl rounded-tr-sm" 
                    : "text-foreground p-0"
                )}>
                  {msg.content}
                </div>
              </div>
            </div>
          ))}

          {/* Current transcript (interim) */}
          {currentTranscript && (
             <div className="flex gap-4 flex-row-reverse">
               <div className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
                 <User className="w-4 h-4" />
               </div>
               <div className="inline-block px-5 py-3 rounded-3xl rounded-tr-sm bg-secondary/50 text-secondary-foreground/70 text-base leading-relaxed italic">
                 {currentTranscript}
                 <span className="inline-block w-1.5 h-4 ml-1 align-middle bg-current animate-pulse"/>
               </div>
             </div>
          )}

          {/* Processing indicator */}
          {isProcessing && (
             <div className="flex gap-4">
               <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                 <Bot className="w-4 h-4" />
               </div>
               <div className="flex items-center gap-2 text-sm text-muted-foreground pt-2">
                 <Loader2 className="w-4 h-4 animate-spin" />
                 <span>Processing response...</span>
               </div>
             </div>
          )}

          <div ref={messagesEndRef} className="h-4" />
      </div>

      {/* Error display */}
      {error && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 px-4 py-2 bg-destructive text-destructive-foreground rounded-full text-sm shadow-lg animate-in fade-in slide-in-from-top-4">
          {error}
        </div>
      )}

      {/* Controls Bar */}
      <div className="p-4 pb-8 border-t bg-background/80 backdrop-blur-sm z-10 flex flex-col items-center gap-4">
         
         <div className="flex items-center gap-2 px-3 py-1 bg-secondary rounded-full text-xs text-muted-foreground">
             <span>Active Voice:</span>
             <select
                value={selectedVoice}
                onChange={(e) => setSelectedVoice(e.target.value)}
                className="bg-transparent border-none focus:ring-0 p-0 text-foreground font-medium cursor-pointer"
              >
                {voices.map(v => (
                  <option key={v.name} value={v.name}>{v.name}</option>
                ))}
              </select>
         </div>

         <div className="flex items-center justify-center gap-6 w-full">
            {isPlaying && (
                <Button
                onClick={stopAudio}
                variant="outline"
                size="icon"
                className="h-12 w-12 rounded-full border-2 border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground transition-all"
                title="Stop Audio"
                >
                <StopCircle className="w-6 h-6" />
                </Button>
            )}

            <Button
                onClick={toggleListening}
                disabled={!speechSupported || isProcessing}
                size="lg"
                className={cn(
                    "h-16 w-16 rounded-full shadow-lg transition-all duration-300",
                    isListening 
                        ? "bg-destructive hover:bg-destructive/90 animate-pulse scale-110" 
                        : "bg-primary hover:bg-primary/90 hover:scale-105"
                )}
            >
                {isListening ? (
                <MicOff className="w-8 h-8" />
                ) : (
                <Mic className="w-8 h-8" />
                )}
            </Button>
         </div>

         <div className="text-sm text-muted-foreground font-medium">
            {isProcessing ? (
              "Thinking..."
            ) : isListening ? (
              <span className="text-destructive">Listening...</span>
            ) : isPlaying ? (
              <span className="text-primary">Speaking...</span>
            ) : (
              "Tap to speak"
            )}
         </div>
      </div>
    </div>
  )
}

