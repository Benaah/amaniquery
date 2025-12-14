"use client"

import { useState, useRef, useEffect, KeyboardEvent } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import {
  Send,
  Paperclip,
  Mic,
  MicOff,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Search,
  Bot,
  BookOpen,
  X
} from "lucide-react"
import type { Attachment } from "./types"

interface AmaniInputProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  onFileSelect?: (files: File[]) => void
  onModeChange?: (mode: "chat" | "hybrid" | "research") => void
  placeholder?: string
  disabled?: boolean
  isLoading?: boolean
  mode?: "chat" | "hybrid" | "research"
  attachments?: Attachment[]
  onRemoveAttachment?: (attachmentId: string) => void
  showModeSelector?: boolean
  enableVoice?: boolean
  isVoiceActive?: boolean
  onVoiceToggle?: () => void
  autocompleteSuggestions?: string[]
  showAutocomplete?: boolean
  onAutocompleteSelect?: (suggestion: string) => void
}

interface ModeOption {
  id: "chat" | "hybrid" | "research"
  label: string
  description: string
  icon: React.ReactNode
  color: string
}

const modeOptions: ModeOption[] = [
  {
    id: "chat",
    label: "Chat",
    description: "General conversation",
    icon: <Bot className="w-4 h-4" />,
    color: "text-blue-600"
  },
  {
    id: "hybrid",
    label: "Hybrid RAG",
    description: "Enhanced with knowledge base",
    icon: <Sparkles className="w-4 h-4" />,
    color: "text-purple-600"
  },
  {
    id: "research",
    label: "Research",
    description: "Deep research mode",
    icon: <Search className="w-4 h-4" />,
    color: "text-green-600"
  }
]

interface AttachmentPreviewProps {
  attachment: Attachment
  onRemove: () => void
}

function AttachmentPreview({ attachment, onRemove }: AttachmentPreviewProps) {
  const getFileIcon = () => {
    switch (attachment.file_type) {
      case "image":
        return <div className="w-8 h-8 bg-blue-100 rounded flex items-center justify-center">🖼️</div>
      case "pdf":
        return <div className="w-8 h-8 bg-red-100 rounded flex items-center justify-center">📄</div>
      case "audio":
        return <div className="w-8 h-8 bg-green-100 rounded flex items-center justify-center">🎵</div>
      case "video":
        return <div className="w-8 h-8 bg-purple-100 rounded flex items-center justify-center">🎥</div>
      default:
        return <div className="w-8 h-8 bg-gray-100 rounded flex items-center justify-center">📎</div>
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  return (
    <div className="flex items-center gap-2 p-2 bg-muted rounded-lg">
      {getFileIcon()}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{attachment.filename}</p>
        <p className="text-xs text-muted-foreground">{formatFileSize(attachment.file_size)}</p>
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
        onClick={onRemove}
      >
        <X className="w-3 h-3" />
      </Button>
    </div>
  )
}

interface AutocompleteDropdownProps {
  suggestions: string[]
  onSelect: (suggestion: string) => void
  onClose: () => void
}

function AutocompleteDropdown({ suggestions, onSelect, onClose }: AutocompleteDropdownProps) {
  return (
    <div className="absolute bottom-full left-0 right-0 mb-2 bg-popover border rounded-lg shadow-lg max-h-48 overflow-y-auto z-10">
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          className="w-full px-4 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
          onClick={() => {
            onSelect(suggestion)
            onClose()
          }}
        >
          {suggestion}
        </button>
      ))}
    </div>
  )
}

export function AmaniInput({
  value,
  onChange,
  onSend,
  onFileSelect,
  onModeChange,
  placeholder = "Ask anything...",
  disabled = false,
  isLoading = false,
  mode = "chat",
  attachments = [],
  onRemoveAttachment,
  showModeSelector = true,
  enableVoice = false,
  isVoiceActive = false,
  onVoiceToggle,
  autocompleteSuggestions = [],
  showAutocomplete = false,
  onAutocompleteSelect
}: AmaniInputProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showModeMenu, setShowModeMenu] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [value])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (!isLoading && value.trim()) {
        onSend()
      }
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      onFileSelect?.(files)
    }
    e.target.value = ""
  }

  const currentMode = modeOptions.find(m => m.id === mode) || modeOptions[0]

  return (
    <div ref={containerRef} className="relative">
      {/* Autocomplete Dropdown */}
      {showAutocomplete && autocompleteSuggestions.length > 0 && (
        <AutocompleteDropdown
          suggestions={autocompleteSuggestions}
          onSelect={onAutocompleteSelect || (() => {})}
          onClose={() => {}}
        />
      )}

      {/* Attachments */}
      {attachments.length > 0 && (
        <div className="mb-3 space-y-2">
          {attachments.map((attachment) => (
            <AttachmentPreview
              key={attachment.id}
              attachment={attachment}
              onRemove={() => onRemoveAttachment?.(attachment.id)}
            />
          ))}
        </div>
      )}

      {/* Main Input */}
      <div className={cn(
        "relative flex items-end gap-2 p-3 bg-card border rounded-2xl transition-all",
        isExpanded && "rounded-b-lg",
        "focus-within:ring-2 focus-within:ring-primary focus-within:border-primary"
      )}>
        {/* Mode Selector */}
        {showModeSelector && onModeChange && (
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              className={cn("h-8 px-2 text-muted-foreground hover:text-foreground", currentMode.color)}
              onClick={() => setShowModeMenu(!showModeMenu)}
            >
              {currentMode.icon}
              <span className="hidden sm:inline ml-1.5 text-xs">{currentMode.label}</span>
              {showModeMenu ? (
                <ChevronUp className="w-3 h-3 ml-1" />
              ) : (
                <ChevronDown className="w-3 h-3 ml-1" />
              )}
            </Button>

            {showModeMenu && (
              <div className="absolute bottom-full left-0 mb-2 w-56 bg-popover border rounded-lg shadow-lg py-1 z-20">
                {modeOptions.map((option) => (
                  <button
                    key={option.id}
                    className={cn(
                      "w-full px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground transition-colors flex items-center gap-3",
                      mode === option.id && "bg-accent text-accent-foreground"
                    )}
                    onClick={() => {
                      onModeChange(option.id)
                      setShowModeMenu(false)
                    }}
                  >
                    {option.icon}
                    <div>
                      <div className="font-medium">{option.label}</div>
                      <div className="text-xs text-muted-foreground">{option.description}</div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Textarea */}
        <div className="flex-1 min-w-0">
          <Textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            className={cn(
              "min-h-[44px] max-h-[200px] resize-none border-0 bg-transparent p-2 focus-visible:ring-0 focus-visible:ring-offset-0 text-sm",
              "placeholder:text-muted-foreground/60"
            )}
            rows={1}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {/* File Upload */}
          {onFileSelect && (
            <>
              <input
                type="file"
                multiple
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
                accept="image/*,audio/*,video/*,.pdf"
              />
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-foreground"
                onClick={() => document.getElementById("file-upload")?.click()}
                disabled={disabled || isLoading}
              >
                <Paperclip className="w-4 h-4" />
              </Button>
            </>
          )}

          {/* Voice Toggle */}
          {enableVoice && onVoiceToggle && (
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "h-8 w-8",
                isVoiceActive ? "text-red-600" : "text-muted-foreground hover:text-foreground"
              )}
              onClick={onVoiceToggle}
              disabled={disabled || isLoading}
            >
              {isVoiceActive ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </Button>
          )}

          {/* Send Button */}
          <Button
            size="icon"
            className="h-8 w-8 rounded-full"
            onClick={onSend}
            disabled={disabled || isLoading || !value.trim()}
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Expanded Options */}
      {isExpanded && (
        <div className="mt-2 p-3 bg-muted rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Advanced options</span>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-muted-foreground hover:text-foreground"
              onClick={() => setIsExpanded(false)}
            >
              <ChevronDown className="w-3 h-3" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}