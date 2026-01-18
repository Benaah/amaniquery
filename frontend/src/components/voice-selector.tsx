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
        className="w-full justify-between h-auto py-2 px-3 border-border hover:bg-secondary/50"
      >
        <div className="flex flex-col items-start text-left">
          <span className="text-sm font-medium">{selectedVoiceInfo?.label || "Select Voice"}</span>
          <span className="text-xs text-muted-foreground">{selectedVoiceInfo?.description}</span>
        </div>
        <ChevronDown
          className={cn(
            "w-4 h-4 transition-transform text-muted-foreground",
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
          <div className="absolute z-20 w-full mt-2 shadow-xl bg-popover border border-border rounded-lg overflow-hidden animate-in fade-in zoom-in-95 duration-100">
            <div className="p-1 max-h-[300px] overflow-y-auto">
              <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Available Voices
              </div>
              <div className="space-y-0.5">
                {OPENAI_VOICES.map((voice) => (
                  <button
                    key={voice.value}
                    onClick={() => {
                      onVoiceChange(voice.value)
                      setIsOpen(false)
                    }}
                    className={cn(
                      "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                      "hover:bg-secondary flex items-center justify-between group",
                      selectedVoice === voice.value && "bg-secondary"
                    )}
                  >
                    <div className="flex flex-col">
                      <span className={cn("font-medium", selectedVoice === voice.value ? "text-primary" : "text-foreground")}>
                        {voice.label}
                      </span>
                      <span className="text-xs text-muted-foreground group-hover:text-muted-foreground/80">{voice.description}</span>
                    </div>
                    {selectedVoice === voice.value && (
                      <Check className="w-4 h-4 text-primary" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

