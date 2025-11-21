"use client"

import { useState } from "react"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Bold, Italic, List, Link as LinkIcon, Image as ImageIcon } from "lucide-react"

interface BlogEditorProps {
  markdownContent: string
  htmlContent: string
  onMarkdownChange: (value: string) => void
  onHtmlChange: (value: string) => void
  mode?: "markdown" | "html" | "both"
}

export function BlogEditor({
  markdownContent,
  htmlContent,
  onMarkdownChange,
  onHtmlChange,
  mode = "both",
}: BlogEditorProps) {
  const [activeTab, setActiveTab] = useState<"markdown" | "html">("markdown")

  const insertMarkdown = (before: string, after: string = "") => {
    const textarea = document.getElementById("markdown-editor") as HTMLTextAreaElement
    if (!textarea) return

    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const selectedText = markdownContent.substring(start, end)
    const newText =
      markdownContent.substring(0, start) +
      before +
      selectedText +
      after +
      markdownContent.substring(end)

    onMarkdownChange(newText)

    // Restore cursor position
    setTimeout(() => {
      textarea.focus()
      const newCursorPos = start + before.length + selectedText.length + after.length
      textarea.setSelectionRange(newCursorPos, newCursorPos)
    }, 0)
  }

  const markdownButtons = [
    { icon: Bold, action: () => insertMarkdown("**", "**"), label: "Bold" },
    { icon: Italic, action: () => insertMarkdown("*", "*"), label: "Italic" },
    { icon: List, action: () => insertMarkdown("- ", ""), label: "List" },
    {
      icon: LinkIcon,
      action: () => insertMarkdown("[", "](url)"),
      label: "Link",
    },
    {
      icon: ImageIcon,
      action: () => insertMarkdown("![alt text](", ")"),
      label: "Image",
    },
  ]

  if (mode === "markdown") {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Markdown Editor</CardTitle>
            <div className="flex gap-2">
              {markdownButtons.map((btn) => {
                const Icon = btn.icon
                return (
                  <Button
                    key={btn.label}
                    variant="ghost"
                    size="sm"
                    onClick={btn.action}
                    title={btn.label}
                  >
                    <Icon className="w-4 h-4" />
                  </Button>
                )
              })}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Textarea
            id="markdown-editor"
            value={markdownContent}
            onChange={(e) => onMarkdownChange(e.target.value)}
            placeholder="Write your post in Markdown..."
            className="min-h-[400px] font-mono"
          />
        </CardContent>
      </Card>
    )
  }

  if (mode === "html") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>HTML Editor</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            value={htmlContent}
            onChange={(e) => onHtmlChange(e.target.value)}
            placeholder="Write your post in HTML..."
            className="min-h-[400px] font-mono"
          />
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Markdown Editor</CardTitle>
            <div className="flex gap-2">
              {markdownButtons.map((btn) => {
                const Icon = btn.icon
                return (
                  <Button
                    key={btn.label}
                    variant="ghost"
                    size="sm"
                    onClick={btn.action}
                    title={btn.label}
                  >
                    <Icon className="w-4 h-4" />
                  </Button>
                )
              })}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Textarea
            id="markdown-editor"
            value={markdownContent}
            onChange={(e) => onMarkdownChange(e.target.value)}
            placeholder="Write your post in Markdown..."
            className="min-h-[300px] font-mono"
          />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>HTML Editor (Optional)</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            value={htmlContent}
            onChange={(e) => onHtmlChange(e.target.value)}
            placeholder="Write your post in HTML (or leave empty to auto-generate from Markdown)..."
            className="min-h-[300px] font-mono"
          />
        </CardContent>
      </Card>
    </div>
  )
}

