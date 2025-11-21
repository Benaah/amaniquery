"use client"

import { useState, useEffect, useRef, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Code, Play, Square } from "lucide-react"

interface AnimatedIDEProps {
  className?: string
}

const pythonCode = `import requests

# Query the AmaniQuery API
response = requests.post(
    "http://localhost:8000/query",
    json={
        "query": "What are the recent parliamentary debates?",
        "top_k": 5,
        "category": "Parliament"
    }
)

# Get the response
data = response.json()
print(f"Answer: {data['answer']}")
print(f"Sources: {len(data.get('sources', []))} found")`

const javascriptCode = `// Using fetch API
const response = await fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'What are the recent parliamentary debates?',
    top_k: 5,
    category: 'Parliament'
  })
});

// Parse and display results
const data = await response.json();
console.log('Answer:', data.answer);
console.log('Sources:', data.sources?.length || 0);`

export function AnimatedIDE({ className }: AnimatedIDEProps) {
  const [language, setLanguage] = useState<"python" | "javascript">("python")
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentLineIndex, setCurrentLineIndex] = useState(0)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const code = language === "python" ? pythonCode : javascriptCode
  const lines = code.split("\n")

  // Derive displayed code from currentLineIndex instead of storing it
  const displayedLines = useMemo(() => {
    if (currentLineIndex > 0 && currentLineIndex <= lines.length) {
      return lines.slice(0, currentLineIndex).join("\n")
    }
    return ""
  }, [currentLineIndex, lines])

  useEffect(() => {
    if (!isPlaying) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }
    
    intervalRef.current = setInterval(() => {
      setCurrentLineIndex((prev) => {
        if (prev >= lines.length) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, 300) // Speed of typing each line

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [isPlaying, lines.length])

  const handleLanguageChange = (lang: "python" | "javascript") => {
    setLanguage(lang)
    setIsPlaying(false)
    setCurrentLineIndex(0)
  }

  const handlePlay = () => {
    if (isPlaying) {
      setIsPlaying(false)
    } else {
      // Reset before starting
      setCurrentLineIndex(0)
      setIsPlaying(true)
    }
  }

  const handleReset = () => {
    setIsPlaying(false)
    setCurrentLineIndex(0)
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center">
            <Code className="w-5 h-5 mr-2" />
            Live Code Demo
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant={language === "python" ? "default" : "outline"}
              size="sm"
              onClick={() => handleLanguageChange("python")}
            >
              Python
            </Button>
            <Button
              variant={language === "javascript" ? "default" : "outline"}
              size="sm"
              onClick={() => handleLanguageChange("javascript")}
            >
              JavaScript
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative">
          {/* IDE Window */}
          <div className="bg-[#1e1e1e] rounded-lg overflow-hidden border border-border">
            {/* Title Bar */}
            <div className="bg-[#2d2d2d] px-4 py-2 flex items-center gap-2 border-b border-border">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
              </div>
              <span className="text-xs text-muted-foreground ml-2">
                {language === "python" ? "main.py" : "main.js"}
              </span>
            </div>

            {/* Code Area */}
            <div className="p-4 font-mono text-sm">
              <pre className="text-[#d4d4d4]">
                <code>
                  {displayedLines.split("\n").map((line, idx) => (
                    <div
                      key={idx}
                      className={`flex items-start ${
                        isPlaying && idx === currentLineIndex - 1 ? "animate-pulse" : ""
                      }`}
                    >
                      <span className="text-[#858585] mr-4 select-none w-6 text-right">
                        {idx + 1}
                      </span>
                      <span className="flex-1">
                        {line}
                      </span>
                    </div>
                  ))}
                  {isPlaying && currentLineIndex < lines.length && (
                    <div className="flex items-start">
                      <span className="text-[#858585] mr-4 select-none w-6 text-right">
                        {currentLineIndex + 1}
                      </span>
                      <span className="flex-1">
                        <span className="inline-block w-2 h-4 bg-[#d4d4d4] animate-pulse"></span>
                      </span>
                    </div>
                  )}
                </code>
              </pre>
            </div>

            {/* Controls */}
            <div className="bg-[#2d2d2d] px-4 py-2 flex items-center justify-between border-t border-border">
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handlePlay}
                  className="h-7 px-3"
                >
                  {isPlaying ? (
                    <>
                      <Square className="w-3 h-3 mr-1" />
                      Stop
                    </>
                  ) : (
                    <>
                      <Play className="w-3 h-3 mr-1" />
                      Play
                    </>
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleReset}
                  className="h-7 px-3"
                  disabled={isPlaying}
                >
                  Reset
                </Button>
              </div>
              <div className="text-xs text-muted-foreground">
                {language === "python" ? "🐍 Python" : "🟨 JavaScript"}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

