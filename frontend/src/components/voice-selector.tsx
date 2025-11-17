"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ChevronDown, Check } from "lucide-react"
import { cn } from "@/lib/utils"

export type OpenAIVoice = "alloy" | "echo" | "fable" | "onyx" | "nova" | "shimmer"

export const OPENAI_VOICES: { value: OpenAIVoice; label: string; description: string }[] = [
  { value: "alloy", label: "Alloy", description: "Neutral, balanced voice" },
  { value: "echo", label: "Echo", description: "Clear and articulate" },
  { value: "fable", label: "Fable", description: "Warm and expressive" },
  { value: "onyx", label: "Onyx", description: "Deep and resonant" },
  { value: "nova", label: "Nova", description: "Bright and energetic" },
  { value: "shimmer", label: "Shimmer", description: "Soft and gentle" },
]

interface VoiceSelectorProps {
  selectedVoice: OpenAIVoice
  onVoiceChange: (voice: OpenAIVoice) => void
  disabled?: boolean
  className?: string
}

export function VoiceSelector({
  selectedVoice,
  onVoiceChange,
  disabled = false,
  className,
}: VoiceSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)

  const selectedVoiceInfo = OPENAI_VOICES.find((v) => v.value === selectedVoice)

  return (
    <div className={cn("relative", className)}>
      <Button
        variant="outline"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className="w-full justify-between"
      >
        <div className="flex flex-col items-start">
          <span className="text-sm font-medium">{selectedVoiceInfo?.label || "Select Voice"}</span>
          <span className="text-xs text-muted-foreground">{selectedVoiceInfo?.description}</span>
        </div>
        <ChevronDown
          className={cn(
            "w-4 h-4 transition-transform",
            isOpen && "transform rotate-180"
          )}
        />
      </Button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <Card className="absolute z-20 w-full mt-2 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Select Voice</CardTitle>
            </CardHeader>
            <CardContent className="p-2">
              <div className="space-y-1">
                {OPENAI_VOICES.map((voice) => (
                  <button
                    key={voice.value}
                    onClick={() => {
                      onVoiceChange(voice.value)
                      setIsOpen(false)
                    }}
                    className={cn(
                      "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                      "hover:bg-accent hover:text-accent-foreground",
                      "flex items-center justify-between",
                      selectedVoice === voice.value && "bg-accent"
                    )}
                  >
                    <div className="flex flex-col">
                      <span className="font-medium">{voice.label}</span>
                      <span className="text-xs text-muted-foreground">{voice.description}</span>
                    </div>
                    {selectedVoice === voice.value && (
                      <Check className="w-4 h-4 text-primary" />
                    )}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

