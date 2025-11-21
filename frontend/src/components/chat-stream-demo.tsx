"use client"

import { useState, useEffect, useRef, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, Play, Square, RotateCcw } from "lucide-react"

interface ChatStreamDemoProps {
  className?: string
}

type ChatMode = "normal" | "hybrid" | "research"

const chatModes: Record<ChatMode, { name: string; description: string; color: string }> = {
  normal: {
    name: "Normal",
    description: "Standard RAG query with vector search",
    color: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  },
  hybrid: {
    name: "Hybrid",
    description: "Enhanced retrieval with hybrid encoder",
    color: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  },
  research: {
    name: "Research",
    description: "Deep research with multiple sources",
    color: "bg-green-500/10 text-green-500 border-green-500/20",
  },
}

const demoResponses: Record<ChatMode, string> = {
  normal: "Based on the parliamentary records, the Finance Bill 2024 has been a major topic of discussion. The bill proposes several tax reforms including...",
  hybrid: "Using enhanced hybrid retrieval, I found comprehensive information across multiple sources. The Finance Bill 2024 discussion spans several parliamentary sessions, with key debates focusing on tax reforms, housing levies, and economic impact assessments. Cross-referencing with constitutional provisions...",
  research: "After conducting deep research across parliamentary records, constitutional documents, and related legislation, here's a comprehensive analysis: The Finance Bill 2024 represents a significant legislative proposal with implications across multiple sectors. Key findings include: 1) Tax policy changes affecting... 2) Constitutional alignment considerations... 3) Public sentiment analysis...",
}

export function ChatStreamDemo({ className }: ChatStreamDemoProps) {
  const [mode, setMode] = useState<ChatMode>("normal")
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentCharIndex, setCurrentCharIndex] = useState(0)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const response = demoResponses[mode]

  // Derive displayed text from currentCharIndex instead of storing it
  const displayedText = useMemo(() => {
    if (currentCharIndex > 0 && currentCharIndex <= response.length) {
      return response.substring(0, currentCharIndex)
    }
    return ""
  }, [currentCharIndex, response])

  useEffect(() => {
    if (!isStreaming) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }
    
    intervalRef.current = setInterval(() => {
      setCurrentCharIndex((prev) => {
        if (prev >= response.length) {
          setIsStreaming(false)
          return prev
        }
        return prev + 1
      })
    }, 30) // Character-by-character streaming speed

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [isStreaming, response])

  const handleModeChange = (newMode: ChatMode) => {
    setMode(newMode)
    setIsStreaming(false)
    setCurrentCharIndex(0)
  }

  const handlePlay = () => {
    if (isStreaming) {
      setIsStreaming(false)
    } else {
      // Reset before starting
      setCurrentCharIndex(0)
      setIsStreaming(true)
    }
  }

  const handleReset = () => {
    setIsStreaming(false)
    setCurrentCharIndex(0)
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center">
            <MessageSquare className="w-5 h-5 mr-2" />
            Chat Stream Demo
          </CardTitle>
          <div className="flex items-center gap-2">
            {(Object.keys(chatModes) as ChatMode[]).map((m) => (
              <Button
                key={m}
                variant={mode === m ? "default" : "outline"}
                size="sm"
                onClick={() => handleModeChange(m)}
                className="text-xs"
              >
                {chatModes[m].name}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Mode Info */}
          <div className={`p-3 rounded-lg border ${chatModes[mode].color}`}>
            <div className="flex items-center justify-between mb-1">
              <Badge variant="outline" className={chatModes[mode].color}>
                {chatModes[mode].name} Mode
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              {chatModes[mode].description}
            </p>
          </div>

          {/* Chat Interface */}
          <div className="bg-muted rounded-lg p-4 min-h-[200px] flex flex-col">
            {/* User Message */}
            <div className="mb-4 flex justify-end">
              <div className="bg-primary text-primary-foreground rounded-lg px-4 py-2 max-w-[80%]">
                <p className="text-sm">
                  What are the recent parliamentary debates on the Finance Bill?
                </p>
              </div>
            </div>

            {/* AI Response */}
            <div className="flex justify-start">
              <div className="bg-background border rounded-lg px-4 py-2 max-w-[80%]">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                  <span className="text-xs text-muted-foreground">AmaniQuery AI</span>
                </div>
                <p className="text-sm whitespace-pre-wrap">
                  {displayedText}
                  {isStreaming && (
                    <span className="inline-block w-2 h-4 bg-foreground animate-pulse ml-1"></span>
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                variant="default"
                size="sm"
                onClick={handlePlay}
                disabled={isStreaming && currentCharIndex >= response.length}
              >
                {isStreaming ? (
                  <>
                    <Square className="w-4 h-4 mr-2" />
                    Stop
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Start Stream
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
                disabled={isStreaming}
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset
              </Button>
            </div>
            <div className="text-xs text-muted-foreground">
              {isStreaming ? "Streaming..." : "Ready"}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

