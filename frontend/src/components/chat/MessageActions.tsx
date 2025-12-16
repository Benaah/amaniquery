"use client"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Copy,
  RotateCw,
  ThumbsUp,
  ThumbsDown,
  Share2,
  Download,
  Edit,
  MoreVertical,
  Check,
  X,
  FileText,
  Image,
  Link2
} from "lucide-react"
import type { Message } from "./types"

interface MessageActionsProps {
  message: Message
  onCopy: (content: string) => void
  onRegenerate: (messageId: string) => void
  onFeedback: (messageId: string, type: "like" | "dislike") => void
  onShare: (message: Message) => void
  onGeneratePDF?: (messageId: string) => void
  onGenerateWord?: (messageId: string) => void
  onEdit?: (message: Message) => void
  className?: string
  showFeedback?: boolean
  compact?: boolean
}

interface ActionButtonProps {
  icon: React.ReactNode
  label: string
  onClick: () => void
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
  className?: string
  isActive?: boolean
}

function ActionButton({ icon, label, onClick, variant = "ghost", className, isActive }: ActionButtonProps) {
  return (
    <Button
      variant={variant}
      size="sm"
      className={cn(
        "h-8 px-2.5 text-muted-foreground hover:text-foreground transition-colors",
        isActive && "bg-accent text-accent-foreground",
        className
      )}
      onClick={onClick}
      title={label}
    >
      {icon}
      <span className="hidden sm:inline ml-1.5 text-xs">{label}</span>
    </Button>
  )
}

export function MessageActions({
  message,
  onCopy,
  onRegenerate,
  onFeedback,
  onShare,
  onGeneratePDF,
  onGenerateWord,
  onEdit,
  className,
  showFeedback = true,
  compact = false
}: MessageActionsProps) {
  const [hasCopied, setHasCopied] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleCopy = async () => {
    await onCopy(message.content)
    setHasCopied(true)
    setTimeout(() => setHasCopied(false), 2000)
    setShowMenu(false)
  }

  const handleRegenerate = () => {
    onRegenerate(message.id)
    setShowMenu(false)
  }

  const handleFeedback = (type: "like" | "dislike") => {
    onFeedback(message.id, type)
    setShowMenu(false)
  }

  const handleShare = () => {
    onShare(message)
    setShowMenu(false)
  }

  const handleGeneratePDF = () => {
    onGeneratePDF?.(message.id)
    setShowMenu(false)
  }

  const handleGenerateWord = () => {
    onGenerateWord?.(message.id)
    setShowMenu(false)
  }

  const handleEdit = () => {
    onEdit?.(message)
    setShowMenu(false)
  }

  if (message.role === "user") {
    return (
      <div className={cn("flex items-center gap-1", className)}>
        <ActionButton
          icon={hasCopied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
          label="Copy"
          onClick={handleCopy}
          isActive={hasCopied}
        />
        {onEdit && (
          <ActionButton
            icon={<Edit className="w-3 h-3" />}
            label="Edit"
            onClick={handleEdit}
          />
        )}
      </div>
    )
  }

  if (compact) {
    return (
      <div className={cn("flex items-center gap-1", className)}>
        <ActionButton
          icon={hasCopied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
          label="Copy"
          onClick={handleCopy}
          isActive={hasCopied}
        />
        <ActionButton
          icon={<RotateCw className="w-3 h-3" />}
          label="Regenerate"
          onClick={handleRegenerate}
        />
        {showFeedback && (
          <>
            <ActionButton
              icon={<ThumbsUp className="w-3 h-3" />}
              label="Like"
              onClick={() => handleFeedback("like")}
              isActive={message.feedback_type === "like"}
            />
            <ActionButton
              icon={<ThumbsDown className="w-3 h-3" />}
              label="Dislike"
              onClick={() => handleFeedback("dislike")}
              isActive={message.feedback_type === "dislike"}
            />
          </>
        )}
        <div className="relative" ref={menuRef}>
          <ActionButton
            icon={<MoreVertical className="w-3 h-3" />}
            label="More"
            onClick={() => setShowMenu(!showMenu)}
          />
          {showMenu && (
            <div className="absolute right-0 top-full mt-1 w-48 bg-popover border rounded-lg shadow-lg py-1 z-50">
              <button
                className="w-full px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground flex items-center gap-2"
                onClick={handleShare}
              >
                <Share2 className="w-4 h-4" />
                Share
              </button>
              {onGeneratePDF && (
                <button
                  className="w-full px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground flex items-center gap-2"
                  onClick={handleGeneratePDF}
                >
                  <FileText className="w-4 h-4" />
                  Export as PDF
                </button>
              )}
              {onGenerateWord && (
                <button
                  className="w-full px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground flex items-center gap-2"
                  onClick={handleGenerateWord}
                >
                  <FileText className="w-4 h-4" />
                  Export as Word
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={cn("flex items-center gap-2 flex-wrap", className)}>
      <ActionButton
        icon={hasCopied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
        label="Copy"
        onClick={handleCopy}
        isActive={hasCopied}
      />
      <ActionButton
        icon={<RotateCw className="w-3 h-3" />}
        label="Regenerate"
        onClick={handleRegenerate}
      />
      {showFeedback && (
        <>
          <ActionButton
            icon={<ThumbsUp className="w-3 h-3" />}
            label="Like"
            onClick={() => handleFeedback("like")}
            isActive={message.feedback_type === "like"}
          />
          <ActionButton
            icon={<ThumbsDown className="w-3 h-3" />}
            label="Dislike"
            onClick={() => handleFeedback("dislike")}
            isActive={message.feedback_type === "dislike"}
          />
        </>
      )}
      <ActionButton
        icon={<Share2 className="w-3 h-3" />}
        label="Share"
        onClick={handleShare}
      />
      {onGeneratePDF && (
        <ActionButton
          icon={<FileText className="w-3 h-3" />}
          label="PDF"
          onClick={handleGeneratePDF}
        />
      )}
      {onGenerateWord && (
        <ActionButton
          icon={<FileText className="w-3 h-3" />}
          label="Word"
          onClick={handleGenerateWord}
        />
      )}
    </div>
  )
}