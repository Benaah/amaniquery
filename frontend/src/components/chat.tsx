"use client"

import { useState, useEffect, useCallback, useRef, type ReactNode } from "react"
import Link from "next/link"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeRaw from "rehype-raw"
import rehypeHighlight from "rehype-highlight"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Bot,
  ChevronDown,
  ChevronUp,
  ArrowUpRight,
  Copy,
  Download,
  ExternalLink,
  Facebook,
  FileText,
  History,
  Link2,
  Linkedin,
  Loader2,
  MessageSquare,
  Mic,
  Paperclip,
  Plus,
  Search,
  Send,
  Settings,
  Share2,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  Trash2,
  Twitter,
  User,
  X
} from "lucide-react"

interface Message {
  id: string
  session_id: string
  role: "user" | "assistant"
  content: string
  created_at: string
  token_count?: number
  model_used?: string
  sources?: Array<{
    title: string
    url: string
    source_name: string
    category: string
    excerpt: string
  }>
  feedback_type?: "like" | "dislike"
  saved?: boolean
}

interface Source {
  title: string
  url: string
  source_name: string
  category: string
  excerpt: string
}

interface ChatSession {
  id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

interface StreamMetadata {
  token_count?: number
  model_used?: string
  sources?: Array<{
    title: string
    url: string
    source_name: string
    category: string
    excerpt: string
  }>
}

type SharePlatform = "twitter" | "linkedin" | "facebook"

interface ShareFormatResponse {
  platform: SharePlatform
  content: string | string[]
  character_count?: number
  hashtags?: string[]
  metadata?: Record<string, unknown>
}

interface ShareSheetState {
  messageId: string
  platform: SharePlatform
  preview?: ShareFormatResponse | null
  isLoading: boolean
  shareLink?: string | null
  shareLinkLoading?: boolean
  posting?: boolean
  shareError?: string | null
  success?: string | null
}

const SHARE_PLATFORMS: Array<{
  id: SharePlatform
  label: string
  accent: string
  description: string
  icon: ReactNode
}> = [
  {
    id: "twitter",
    label: "X / Twitter",
    accent: "from-[#1d1d1f] to-[#111] text-white",
    description: "Real-time legal insights (280 chars)",
    icon: <Twitter className="w-4 h-4" />
  },
  {
    id: "linkedin",
    label: "LinkedIn",
    accent: "from-[#0A66C2] to-[#004182] text-white",
    description: "Professional analysis (3,000 chars)",
    icon: <Linkedin className="w-4 h-4" />
  },
  {
    id: "facebook",
    label: "Facebook",
    accent: "from-[#1877F2] to-[#0F5EC7] text-white",
    description: "Community-friendly summaries",
    icon: <Facebook className="w-4 h-4" />
  }
]

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [chatHistory, setChatHistory] = useState<ChatSession[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [showSources, setShowSources] = useState(false)
  const [isResearchMode, setIsResearchMode] = useState(false)
  const [researchResults, setResearchResults] = useState<Record<string, unknown>>({})
  const [shareSheet, setShareSheet] = useState<ShareSheetState | null>(null)
  const [shareCache, setShareCache] = useState<
    Record<string, Partial<Record<SharePlatform, ShareFormatResponse>>>
  >({})
  const messagesContainerRef = useRef<HTMLDivElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  const scrollMessagesToBottom = useCallback(
    (behavior: ScrollBehavior = "smooth") => {
      requestAnimationFrame(() => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTo({
            top: messagesContainerRef.current.scrollHeight,
            behavior
          })
        }
        messagesEndRef.current?.scrollIntoView({ behavior, block: "end" })
      })
    },
    []
  )

  useEffect(() => {
    scrollMessagesToBottom(messages.length < 3 ? "instant" : "smooth")
  }, [messages, isLoading, scrollMessagesToBottom])

  const findPreviousUserPrompt = useCallback(
    (messageId: string) => {
      const index = messages.findIndex((msg) => msg.id === messageId)
      if (index === -1) return undefined
      for (let i = index - 1; i >= 0; i--) {
        if (messages[i].role === "user") {
          return messages[i].content
        }
      }
      return undefined
    },
    [messages]
  )

  const loadChatHistory = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/sessions`)
      if (response.ok) {
        const sessions = await response.json()
        setChatHistory(sessions)
      }
    } catch (error) {
      console.error("Failed to load chat history:", error)
    }
  }, [API_BASE_URL])

  // Load chat history on component mount
  useEffect(() => {
    loadChatHistory()
  }, [loadChatHistory])

  const createNewSession = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "New Chat" })
      })
      if (response.ok) {
        const session = await response.json()
        setCurrentSessionId(session.id)
        setMessages([])
        loadChatHistory()
        return session.id
      }
    } catch (error) {
      console.error("Failed to create session:", error)
    }
    return null
  }

  const loadSession = async (sessionId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`)
      if (response.ok) {
        const sessionMessages = await response.json()
        setMessages(sessionMessages)
        setCurrentSessionId(sessionId)
        setShowHistory(false)
      }
    } catch (error) {
      console.error("Failed to load session:", error)
    }
  }

  const sendMessage = async (content: string) => {
    if (!content.trim()) return

    let sessionId = currentSessionId
    if (!sessionId) {
      sessionId = await createNewSession()
      if (!sessionId) return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      session_id: sessionId,
      role: "user",
      content: content.trim(),
      created_at: new Date().toISOString(),
      saved: false
    }

    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      let response;
      if (isResearchMode) {
        // Use research endpoints for research mode (non-streaming)
        response = await fetch(`${API_BASE_URL}/research/analyze-legal-query`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({
            query: content.trim()
          })
        })
      } else {
        // Use streaming chat endpoint
        response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: content.trim(),
            role: "user",
            stream: true
          })
        })
      }

      if (response.ok) {
        if (isResearchMode) {
          // Handle non-streaming research response
          const data = await response.json()
          // Format research response with better structure and null safety
          const analysis = data.analysis || {}
          
          // Extract sections safely
          const queryInterpretation = analysis.query_interpretation || 'Analyzing your legal question...'
          const applicableLaws = analysis.applicable_laws || 'Researching relevant Kenyan laws...'
          const legalAnalysis = analysis.legal_analysis || 'Conducting detailed legal analysis...'
          const practicalGuidance = analysis.practical_guidance || 'Developing practical guidance...'
          const additionalConsiderations = analysis.additional_considerations || 'Reviewing additional legal considerations...'
          
          const researchContent = `
## 📋 Legal Research Analysis

**Your Question:** ${data.original_query || content.trim()}

---

### 🔍 Query Understanding
${queryInterpretation}

---

### 📖 Applicable Laws & Provisions
${applicableLaws}

---

### ⚖️ Legal Analysis
${legalAnalysis}

---

### 🛠️ Practical Guidance
${practicalGuidance}

---

### ⚠️ Important Considerations
${additionalConsiderations}

---

### 📝 Disclaimer
*This analysis is for informational purposes only and does not constitute legal advice. Please consult with a qualified legal professional for advice specific to your situation.*
          `.trim()
          
          const assistantMessage: Message = {
            id: Date.now().toString(),
            session_id: sessionId,
            role: "assistant",
            content: researchContent,
            created_at: new Date().toISOString(),
            model_used: data.model_used || "gemini-research",
            saved: true
          }
          setMessages(prev => [...prev, assistantMessage])
          
          // Store research results for document generation
          setResearchResults(prev => ({
            ...prev,
            [assistantMessage.id]: data
          }))
        } else {
          // Handle streaming response
          const assistantMessageId = Date.now().toString()
          const assistantMessage: Message = {
            id: assistantMessageId,
            session_id: sessionId,
            role: "assistant",
            content: "",
            created_at: new Date().toISOString(),
            model_used: "streaming",
            saved: false
          }
          
          // Add initial empty assistant message
          setMessages(prev => [...prev, assistantMessage])
          
          const reader = response.body?.getReader()
          const decoder = new TextDecoder()
          let accumulatedContent = ""
          const metadata: StreamMetadata = {}
          
          if (reader) {
            try {
              while (true) {
                const { done, value } = await reader.read()
                if (done) break
                
                const chunk = decoder.decode(value, { stream: true })
                const lines = chunk.split('\n')
                
                for (const line of lines) {
                  if (line.startsWith('data: ')) {
                    const data = line.slice(6)
                    if (data === '[DONE]') continue
                    
                    try {
                      const parsed = JSON.parse(data)
                      
                      if (parsed.type === 'sources') {
                        // Store sources metadata
                        metadata.sources = parsed.sources
                        metadata.token_count = parsed.retrieved_chunks
                        metadata.model_used = parsed.model_used
                      } else if (parsed.type === 'content') {
                        // Accumulate content chunks
                        accumulatedContent += parsed.content
                        // Update message content in real-time
                        setMessages(prev => prev.map(msg => 
                          msg.id === assistantMessageId 
                            ? { ...msg, content: accumulatedContent }
                            : msg
                        ))
                      } else if (parsed.type === 'done') {
                        // Final update with complete answer
                        setMessages(prev => prev.map(msg => 
                          msg.id === assistantMessageId 
                            ? { 
                                ...msg, 
                                content: parsed.full_answer || accumulatedContent,
                                token_count: metadata.token_count,
                                model_used: metadata.model_used,
                                sources: metadata.sources,
                                saved: true
                              }
                            : msg
                        ))
                        break
                      } else if (parsed.type === 'error') {
                        // Handle streaming error
                        console.error('Streaming error:', parsed.error)
                        setMessages(prev => prev.map(msg => 
                          msg.id === assistantMessageId 
                            ? { 
                                ...msg, 
                                content: `Error: ${parsed.error}`,
                                model_used: 'error',
                                saved: true
                              }
                            : msg
                        ))
                        break
                      }
                    } catch {
                      // Skip invalid JSON chunks
                      continue
                    }
                  }
                }
              }
            } finally {
              reader.releaseLock()
            }
          }
        }
        loadChatHistory() // Refresh history to update message count
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          session_id: sessionId,
          role: "assistant",
          content: isResearchMode 
            ? "Sorry, I encountered an error processing your legal research request."
            : "Sorry, I encountered an error processing your request.",
          created_at: new Date().toISOString()
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      console.error("Failed to send message:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        session_id: sessionId,
        role: "assistant",
        content: isResearchMode 
          ? "Sorry, I couldn't connect to the research service. Please try again."
          : "Sorry, I couldn't connect to the server. Please try again.",
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const submitFeedback = async (messageId: string, feedbackType: "like" | "dislike") => {
    console.log("Submitting feedback for message:", messageId, "type:", feedbackType)
    try {
      const response = await fetch(`${API_BASE_URL}/chat/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message_id: messageId,
          feedback_type: feedbackType
        })
      })
      
      if (response.ok) {
        console.log("Feedback submitted successfully")
        // Update local message state
        setMessages(prev => prev.map(msg => 
          msg.id === messageId ? { ...msg, feedback_type: feedbackType } : msg
        ))
      } else {
        console.error("Feedback submission failed:", response.status, await response.text())
      }
    } catch (error) {
      console.error("Failed to submit feedback:", error)
    }
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success("Message copied to clipboard!")
    } catch (error) {
      console.error("Failed to copy to clipboard:", error)
      toast.error("Failed to copy to clipboard")
    }
  }

  const deleteSession = async (sessionId: string) => {
    if (!confirm("Are you sure you want to delete this chat session? This action cannot be undone.")) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
        method: "DELETE"
      })
      
      if (response.ok) {
        // Remove from local state
        setChatHistory(prev => prev.filter(session => session.id !== sessionId))
        // If current session was deleted, clear it
        if (currentSessionId === sessionId) {
          setCurrentSessionId(null)
          setMessages([])
        }
      } else {
        console.error("Failed to delete session:", response.status)
      }
    } catch (error) {
      console.error("Failed to delete session:", error)
    }
  }

  const shareChat = async (options: { silent?: boolean } = {}) => {
    if (!currentSessionId) return null

    try {
      const response = await fetch(
        `${API_BASE_URL}/chat/share?session_id=${encodeURIComponent(currentSessionId)}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        }
      )
      if (response.ok) {
        const data = await response.json()
        const shareUrl = `${window.location.origin}${data.share_link}`
        if (!options.silent) {
          await navigator.clipboard.writeText(shareUrl)
          toast.success("Share link copied to clipboard!")
        }
        return shareUrl
      } else {
        console.error("Failed to generate share link:", response.status)
        if (!options.silent) {
          toast.error("Failed to generate share link")
        }
      }
    } catch (error) {
      console.error("Failed to generate share link:", error)
      if (!options.silent) {
        toast.error("Failed to generate share link")
      }
    }
    return null
  }

  const generatePDF = async (messageId: string) => {
    const researchData = researchResults[messageId]
    if (!researchData) {
      toast.error("Research data not found")
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/research/generate-pdf-report`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          analysis_results: JSON.stringify(researchData),
          report_title: "Legal Research Report"
        })
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'legal_research_report.pdf'
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        toast.success("PDF report downloaded!")
      } else {
        toast.error("Failed to generate PDF report")
      }
    } catch (error) {
      console.error("Error generating PDF:", error)
      toast.error("Error generating PDF report")
    }
  }

  const generateWord = async (messageId: string) => {
    const researchData = researchResults[messageId]
    if (!researchData) {
      toast.error("Research data not found")
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/research/generate-word-report`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          analysis_results: JSON.stringify(researchData),
          report_title: "Legal Research Report"
        })
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'legal_research_report.docx'
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        toast.success("Word document downloaded!")
      } else {
        toast.error("Failed to generate Word document")
      }
    } catch (error) {
      console.error("Error generating Word document:", error)
      toast.error("Error generating Word document")
    }
  }

  const sanitizeForSharing = (content: string) => {
    if (!content) return ""
    return content.replace(/<[^>]+>/g, "").trim()
  }

  const ensureSharePreview = async (message: Message, platform: SharePlatform) => {
    const cached = shareCache[message.id]?.[platform]
    if (cached) return cached

    try {
      setShareSheet((prev) =>
        prev?.messageId === message.id
          ? { ...prev, isLoading: true, shareError: null, success: null, shareLink: null }
          : prev
      )

      const response = await fetch(`${API_BASE_URL}/share/format`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answer: sanitizeForSharing(message.content),
          sources: message.sources || [],
          platform,
          query: findPreviousUserPrompt(message.id),
          include_hashtags: true
        })
      })

      if (!response.ok) {
        const detail = await response.text()
        throw new Error(detail || "Unable to format response")
      }

      const data: ShareFormatResponse = await response.json()
      setShareCache((prev) => ({
        ...prev,
        [message.id]: { ...(prev[message.id] || {}), [platform]: data }
      }))
      setShareSheet((prev) =>
        prev?.messageId === message.id ? { ...prev, preview: data, isLoading: false } : prev
      )
      return data
    } catch (error) {
      console.error("Failed to format post:", error)
      setShareSheet((prev) =>
        prev?.messageId === message.id
          ? {
              ...prev,
              isLoading: false,
              shareError:
                error instanceof Error ? error.message : "Unable to format this response right now."
            }
          : prev
      )
      return null
    }
  }

  const openShareSheet = (message: Message, platform: SharePlatform = "twitter") => {
    if (message.role !== "assistant") return

    if (shareSheet?.messageId === message.id && shareSheet.platform === platform) {
      setShareSheet(null)
      return
    }

    const cached = shareCache[message.id]?.[platform]
    setShareSheet({
      messageId: message.id,
      platform,
      preview: cached,
      isLoading: !cached,
      shareLink: null,
      shareError: null,
      success: null
    })

    if (!cached) {
      ensureSharePreview(message, platform)
    }
  }

  const changeSharePlatform = (message: Message, platform: SharePlatform) => {
    if (!shareSheet || shareSheet.messageId !== message.id) {
      openShareSheet(message, platform)
      return
    }

    const cached = shareCache[message.id]?.[platform]
    setShareSheet({
      ...shareSheet,
      platform,
      preview: cached,
      isLoading: !cached,
      shareLink: null,
      shareError: null,
      success: null
    })

    if (!cached) {
      ensureSharePreview(message, platform)
    }
  }

  const copyShareContent = async () => {
    if (!shareSheet?.preview) return
    const preview = shareSheet.preview
    const text = Array.isArray(preview.content) ? preview.content.join("\n\n") : preview.content

    try {
      await navigator.clipboard.writeText(text)
      toast.success("Formatted answer copied!")
    } catch (error) {
      console.error("Failed to copy share content:", error)
      toast.error("Unable to copy content")
    }
  }

  const openShareIntent = async (message: Message) => {
    if (!shareSheet) return
    const preview = shareSheet.preview ?? (await ensureSharePreview(message, shareSheet.platform))
    if (!preview) return

    try {
      setShareSheet((prev) =>
        prev ? { ...prev, shareLinkLoading: true, shareError: null, success: null } : prev
      )
      const sessionLink = await shareChat({ silent: true })

      const response = await fetch(`${API_BASE_URL}/share/generate-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          platform: shareSheet.platform,
          content: preview.content,
          url: sessionLink || undefined
        })
      })

      if (!response.ok) {
        const detail = await response.text()
        throw new Error(detail || "Unable to open share dialog")
      }

      const data = await response.json()
      setShareSheet((prev) =>
        prev
          ? {
              ...prev,
              shareLink: data.share_url,
              shareLinkLoading: false,
              success: `Share dialog ready for ${shareSheet.platform}`
            }
          : prev
      )
      window.open(data.share_url, "_blank", "noopener,noreferrer")
    } catch (error) {
      console.error("Failed to open share link:", error)
      setShareSheet((prev) =>
        prev
          ? {
              ...prev,
              shareLinkLoading: false,
              shareError:
                error instanceof Error
                  ? error.message
                  : "Unable to open the platform share dialog."
            }
          : prev
      )
    }
  }

  const postDirectly = async (message: Message) => {
    if (!shareSheet) return
    const preview = shareSheet.preview ?? (await ensureSharePreview(message, shareSheet.platform))
    if (!preview) return

    try {
      setShareSheet((prev) =>
        prev ? { ...prev, posting: true, shareError: null, success: null } : prev
      )

      const response = await fetch(`${API_BASE_URL}/share/post`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          platform: shareSheet.platform,
          content: preview.content,
          message_id: message.id
        })
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || data.message || "Unable to post to platform")
      }

      setShareSheet((prev) =>
        prev
          ? {
              ...prev,
              posting: false,
              success: data.message || "Post created successfully!",
              shareError: null
            }
          : prev
      )
      toast.success(`Posted to ${shareSheet.platform} successfully`)
    } catch (error) {
      console.error("Failed to post to platform:", error)
      setShareSheet((prev) =>
        prev
          ? {
              ...prev,
              posting: false,
              shareError:
                error instanceof Error
                  ? error.message
                  : "Unable to post automatically. Try the share dialog instead."
            }
          : prev
      )
    }
  }

  const formatTimestamp = (dateString: string) => {
    const date = new Date(dateString)
    if (Number.isNaN(date.getTime())) return ""
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  }

  interface SuggestionTile {
    title: string
    description: string
  }

  const suggestedQuestions: SuggestionTile[] = [
    {
      title: "Latest developments in Kenyan constitutional law",
      description: "Get a rapid scan of amendments, rulings, and reforms."
    },
    {
      title: "Recent changes to the Kenyan Penal Code",
      description: "Understand how new provisions impact compliance."
    },
    {
      title: "Key provisions of the Competition Act",
      description: "Summaries on enforcement thresholds and penalties."
    },
    {
      title: "Environmental law cases in Kenyan courts",
      description: "Explore how judges interpret conservation mandates."
    },
    {
      title: "Requirements for starting a business in Kenya",
      description: "Licensing, compliance, and registration checklist."
    }
  ]

  const researchSuggestedQuestions: SuggestionTile[] = [
    {
      title: "Comprehensive analysis of the Bill of Rights",
      description: "Focus on digital rights and emerging jurisprudence."
    },
    {
      title: "Evolution of environmental law in Kenya",
      description: "Trace policy effectiveness against conservation goals."
    },
    {
      title: "Impact of Penal Code amendments on cybercrime",
      description: "Deep dive into enforcement trends and loopholes."
    },
    {
      title: "Devolution framework in the Constitution",
      description: "Assess implementation challenges across counties."
    },
    {
      title: "Data protection and privacy rights landscape",
      description: "Map compliance expectations to ICT deployments."
    }
  ]

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessage(input)
  }

  const formatMessageWithCitations = (content: string, sources?: Source[]) => {
    if (!sources || sources.length === 0) return content

    // Simple citation replacement - look for [1], [2], etc.
    let formattedContent = content
    sources.forEach((source, index) => {
      const citation = `[${index + 1}]`
      formattedContent = formattedContent.replace(
        new RegExp(`\\${citation}`, 'g'),
        `<sup class="text-primary font-semibold">${index + 1}</sup>`
      )
    })

    return formattedContent
  }

  return (
    <div className="relative flex min-h-screen bg-gradient-to-b from-background via-background/95 to-background text-foreground">
      <div className="pointer-events-none absolute inset-0 opacity-60">
        <div className="absolute -top-32 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-primary/20 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-blue-500/10 blur-[120px]" />
      </div>

      <div className="hidden md:flex w-72 border-r border-white/5 bg-black/20 backdrop-blur-xl overflow-y-auto flex-col transition-all duration-300 ease-in-out">
        <div className="p-4 border-b border-white/5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-widest text-muted-foreground">Sessions</p>
              <h3 className="font-semibold text-sm">Chat History</h3>
            </div>
            <Button variant="ghost" size="sm" onClick={createNewSession} className="h-8 w-8 rounded-full">
              <Plus className="w-3 h-3" />
            </Button>
          </div>
          <div className="mt-3 rounded-xl border border-white/5 bg-white/5 px-3 py-2 text-xs text-muted-foreground">
            Quickly relive previous analyses or spin up a fresh thread.
          </div>
        </div>
        <div className="p-3 space-y-2 flex-1">
          {chatHistory.map((session) => (
            <div key={session.id} className="flex items-center space-x-2 p-1 group">
              <Button
                variant={currentSessionId === session.id ? "secondary" : "ghost"}
                className="flex-1 justify-between text-left h-auto px-3 py-2 text-xs transition-all duration-200 rounded-2xl border border-transparent group-hover:border-white/10"
                onClick={() => loadSession(session.id)}
              >
                <div className="flex items-center w-full">
                  <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-white/10 mr-3">
                    <MessageSquare className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate text-xs">
                      {session.title || `Chat ${session.id.slice(-6)}`}
                    </div>
                    <div className="text-[11px] text-muted-foreground">{session.message_count} messages</div>
                  </div>
                </div>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive h-7 w-7 rounded-full p-0 transition-opacity duration-200"
                onClick={() => deleteSession(session.id)}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </div>
          ))}
        </div>
      </div>

      {showHistory && (
        <div className="md:hidden fixed inset-0 z-50 bg-black/70 backdrop-blur-sm" onClick={() => setShowHistory(false)}>
          <div className="absolute left-0 top-0 h-full w-80 bg-background border-r border-white/10 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="p-4 border-b border-white/10">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Chat History</h3>
                <Button variant="ghost" size="sm" onClick={() => setShowHistory(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full mt-2 rounded-xl"
                onClick={() => {
                  createNewSession()
                  setShowHistory(false)
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                New Chat
              </Button>
            </div>
            <div className="p-2 space-y-1 flex-1 overflow-y-auto">
              {chatHistory.map((session) => (
                <div key={session.id} className="flex items-center space-x-2 p-1">
                  <Button
                    variant={currentSessionId === session.id ? "secondary" : "ghost"}
                    className="flex-1 justify-start text-left h-auto p-3"
                    onClick={() => {
                      loadSession(session.id)
                      setShowHistory(false)
                    }}
                  >
                    <MessageSquare className="w-4 h-4 mr-2 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{session.title || `Chat ${session.id.slice(-8)}`}</div>
                      <div className="text-xs text-muted-foreground">{session.message_count} messages</div>
                    </div>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-muted-foreground hover:text-destructive"
                    onClick={() => deleteSession(session.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="flex-1 flex flex-col relative z-10">
        <div className="border-b border-white/5 bg-background/60 backdrop-blur-xl">
          <div className="flex flex-col gap-4 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" className="md:hidden rounded-full" onClick={() => setShowHistory(!showHistory)}>
                  <History className="w-4 h-4" />
                </Button>
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">AmaniQuery</p>
                  <h1 className="text-xl md:text-2xl font-semibold">Conversational Legal Intelligence</h1>
                </div>
                {isResearchMode && (
                  <Badge variant="default" className="bg-blue-600/90">
                    <Search className="w-3 h-3 mr-1" />
                    Research Mode
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant={isResearchMode ? "default" : "outline"}
                  size="sm"
                  onClick={() => setIsResearchMode(!isResearchMode)}
                  className={`h-9 rounded-full px-3 ${isResearchMode ? "bg-blue-600 hover:bg-blue-700" : ""}`}
                >
                  <Search className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">Research Mode</span>
                  <span className="sm:hidden">Research</span>
                </Button>
                {currentSessionId && (
                  <Button variant="outline" size="sm" className="h-9 rounded-full px-3" onClick={() => shareChat()}>
                    <Share2 className="w-4 h-4 mr-2" />
                    <span className="hidden sm:inline">Share Chat</span>
                    <span className="sm:hidden">Share</span>
                  </Button>
                )}
                <Link href="/">
                  <Button variant="outline" size="sm" className="h-9 rounded-full px-3">
                    <Settings className="w-4 h-4 mr-2" />
                    <span className="hidden sm:inline">Home</span>
                    <span className="sm:hidden">Home</span>
                  </Button>
                </Link>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
              <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-primary/10 to-primary/5 px-3 py-2">
                <p className="text-muted-foreground uppercase tracking-wider text-[10px]">Streaming</p>
                <p className="font-semibold">Token-by-token</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
                <p className="text-muted-foreground uppercase tracking-wider text-[10px]">Sources</p>
                <p className="font-semibold">Verifiable citations</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
                <p className="text-muted-foreground uppercase tracking-wider text-[10px]">Mode</p>
                <p className="font-semibold">{isResearchMode ? "Deep research" : "Chat"}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
                <p className="text-muted-foreground uppercase tracking-wider text-[10px]">Share</p>
                <p className="font-semibold">NiruShare ready</p>
              </div>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-hidden">
          <div
            ref={messagesContainerRef}
            className="h-full overflow-y-auto px-3 md:px-8 py-6 space-y-4 scrollbar-thin scrollbar-thumb-white/10"
          >
            {messages.length === 0 && (
              <div className="text-center py-10 md:py-20">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10">
                  <Bot className="h-7 w-7 text-primary" />
                </div>
                <h2 className="text-lg md:text-2xl font-semibold">
                  Welcome to AmaniQuery {isResearchMode && "(Research Mode)"}
                </h2>
                <p className="text-muted-foreground mt-2 text-sm md:text-base max-w-xl mx-auto">
                  {isResearchMode
                    ? "Submit a detailed Kenyan legal question and receive structured analysis built for citations and downstream reporting."
                    : "Ask about Kenyan law, parliament, or current affairs. Answers stream in real time with sources you can trust."}
                </p>
                <div className="mt-8 grid gap-3 md:grid-cols-2 max-w-3xl mx-auto">
                  {(isResearchMode ? researchSuggestedQuestions : suggestedQuestions).map((question) => (
                    <button
                      type="button"
                      key={question.title}
                      onClick={() => sendMessage(question.title)}
                      className="w-full rounded-3xl border border-white/10 bg-white/5 p-4 text-left transition hover:border-primary/40 hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60"
                    >
                      <div className="flex items-start gap-3">
                        <div className="rounded-2xl bg-primary/15 p-2 text-primary">
                          <Sparkles className="w-4 h-4" />
                        </div>
                        <div className="flex-1 space-y-1">
                          <p className="font-semibold text-sm md:text-base leading-tight">{question.title}</p>
                          <p className="text-xs text-muted-foreground md:text-sm">{question.description}</p>
                        </div>
                        <ArrowUpRight className="w-4 h-4 text-muted-foreground" />
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-3`}
              >
                <div
                  className={`flex w-full max-w-3xl ${message.role === "user" ? "flex-row-reverse text-right" : "flex-row"} gap-3`}
                >
                  <div
                    className={`flex-shrink-0 h-10 w-10 rounded-2xl border border-white/10 backdrop-blur flex items-center justify-center ${
                      message.role === "user" ? "bg-primary/90 text-primary-foreground" : "bg-white/5 text-white"
                    }`}
                  >
                    {message.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>
                  <div className="flex-1 space-y-3">
                    <Card
                      className={`rounded-3xl border border-white/5 bg-white/5 text-sm md:text-base shadow-xl ${
                        message.role === "user" ? "bg-primary/90 text-primary-foreground" : "backdrop-blur-xl"
                      }`}
                    >
                      <CardContent className="p-4 md:p-6 space-y-3">
                        <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-wider text-muted-foreground">
                          <span>{message.role === "user" ? "You" : "AmaniQuery"}</span>
                          <span className="h-1 w-1 rounded-full bg-muted-foreground/50" />
                          <span>{formatTimestamp(message.created_at)}</span>
                          {message.model_used && (
                            <>
                              <span className="h-1 w-1 rounded-full bg-muted-foreground/50" />
                              <span className="font-mono text-[11px]">{message.model_used.replace(/_/g, " ")}</span>
                            </>
                          )}
                          {message.token_count && (
                            <>
                              <span className="h-1 w-1 rounded-full bg-muted-foreground/50" />
                              <span>{message.token_count} tokens</span>
                            </>
                          )}
                          {message.sources && message.sources.length > 0 && (
                            <>
                              <span className="h-1 w-1 rounded-full bg-muted-foreground/50" />
                              <span>{message.sources.length} sources</span>
                            </>
                          )}
                        </div>

                        {message.model_used === "gemini-research" && (
                          <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/40 bg-blue-500/10 px-3 py-1 text-xs text-blue-100">
                            <Search className="w-3.5 h-3.5" />
                            Legal Research Report
                          </div>
                        )}

                        <div className="prose prose-sm md:prose-base max-w-none dark:prose-invert text-sm md:text-base">
                          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw, rehypeHighlight]}>
                            {formatMessageWithCitations(message.content, message.sources)}
                          </ReactMarkdown>
                        </div>
                      </CardContent>
                    </Card>

                    {message.role === "assistant" && (
                      <div className={`flex flex-wrap items-center gap-2 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => submitFeedback(message.id, "like")}
                          disabled={!message.saved}
                          className={`h-9 rounded-full px-3 text-xs ${message.feedback_type === "like" ? "text-green-500" : "text-muted-foreground"}`}
                        >
                          <ThumbsUp className="w-4 h-4 mr-1" />
                          Helpful
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => submitFeedback(message.id, "dislike")}
                          disabled={!message.saved}
                          className={`h-9 rounded-full px-3 text-xs ${message.feedback_type === "dislike" ? "text-red-500" : "text-muted-foreground"}`}
                        >
                          <ThumbsDown className="w-4 h-4 mr-1" />
                          Refine
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(message.content)}
                          className="h-9 rounded-full px-3 text-xs text-muted-foreground"
                        >
                          <Copy className="w-4 h-4 mr-1" />
                          Copy
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openShareSheet(message)}
                          disabled={!message.saved}
                          className={`h-9 rounded-full px-3 text-xs ${shareSheet?.messageId === message.id ? "bg-white/10" : "text-muted-foreground"}`}
                        >
                          <Share2 className="w-4 h-4 mr-1" />
                          Share
                        </Button>
                        {message.model_used === "gemini-research" && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => generatePDF(message.id)}
                              disabled={!message.saved}
                              className="h-9 rounded-full px-3 text-xs text-muted-foreground"
                            >
                              <FileText className="w-4 h-4 mr-1" />
                              PDF
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => generateWord(message.id)}
                              disabled={!message.saved}
                              className="h-9 rounded-full px-3 text-xs text-muted-foreground"
                            >
                              <Download className="w-4 h-4 mr-1" />
                              Word
                            </Button>
                          </>
                        )}
                      </div>
                    )}

                    {shareSheet?.messageId === message.id && (
                      <div className="rounded-3xl border border-white/10 bg-background/80 backdrop-blur-xl p-4 md:p-5 space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Social share</p>
                            <h4 className="font-semibold text-sm">Turn this answer into a post</h4>
                          </div>
                          <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full" onClick={() => setShareSheet(null)}>
                            <X className="w-4 h-4" />
                          </Button>
                        </div>

                        <div className="grid gap-2 md:grid-cols-3">
                          {SHARE_PLATFORMS.map((platform) => (
                            <button
                              type="button"
                              key={platform.id}
                              onClick={() => changeSharePlatform(message, platform.id)}
                              className={`group rounded-2xl border border-white/10 p-3 text-left transition hover:border-white/30 ${
                                shareSheet.platform === platform.id ? "bg-white/10" : "bg-white/[0.04]"
                              }`}
                            >
                              <div className={`inline-flex items-center gap-2 rounded-full bg-gradient-to-r ${platform.accent} px-2.5 py-1 text-[11px] font-semibold`}>
                                {platform.icon}
                                {platform.label}
                              </div>
                              <p className="mt-2 text-[11px] text-muted-foreground">{platform.description}</p>
                            </button>
                          ))}
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                          {shareSheet.isLoading && (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Loader2 className="w-4 h-4 animate-spin" />
                              Formatting response for {shareSheet.platform}...
                            </div>
                          )}
                          {!shareSheet.isLoading && shareSheet.preview && (
                            <div className="space-y-2">
                              <p className="text-[11px] uppercase tracking-wider text-muted-foreground">Preview</p>
                              <div className="rounded-xl bg-background/80 border border-white/10 p-3 max-h-64 overflow-auto text-xs md:text-sm whitespace-pre-wrap">
                                {Array.isArray(shareSheet.preview.content)
                                  ? shareSheet.preview.content.join("\n\n")
                                  : shareSheet.preview.content}
                              </div>
                              {shareSheet.preview.hashtags && shareSheet.preview.hashtags.length > 0 && (
                                <div className="flex flex-wrap gap-2 text-[11px] text-primary">
                                  {shareSheet.preview.hashtags.map((tag) => (
                                    <span key={tag} className="rounded-full bg-primary/10 px-2 py-0.5">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                          {shareSheet.shareError && <p className="mt-2 text-xs text-red-500">{shareSheet.shareError}</p>}
                          {shareSheet.success && <p className="mt-2 text-xs text-emerald-400">{shareSheet.success}</p>}
                        </div>

                        <div className="flex flex-wrap gap-2">
                          <Button variant="outline" size="sm" className="rounded-full border-white/20 text-xs" onClick={copyShareContent} disabled={!shareSheet.preview}>
                            <Copy className="w-4 h-4 mr-1" />
                            Copy text
                          </Button>
                          <Button
                            variant="default"
                            size="sm"
                            className="rounded-full text-xs"
                            onClick={() => openShareIntent(message)}
                            disabled={!shareSheet.preview || shareSheet.shareLinkLoading}
                          >
                            {shareSheet.shareLinkLoading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <ExternalLink className="w-4 h-4 mr-1" />}
                            Open share dialog
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="rounded-full text-xs"
                            onClick={() => postDirectly(message)}
                            disabled={!shareSheet.preview || shareSheet.posting}
                          >
                            {shareSheet.posting ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Link2 className="w-4 h-4 mr-1" />}
                            Direct post (beta)
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="flex w-full max-w-3xl items-start gap-3">
                  <div className="flex-shrink-0 h-10 w-10 rounded-2xl border border-white/10 bg-white/5 flex items-center justify-center">
                    <Bot className="w-4 h-4" />
                  </div>
                  <Card className="rounded-3xl border border-white/5 bg-white/5 px-5 py-4">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Streaming response...
                    </div>
                  </Card>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {messages.length > 0 && messages[messages.length - 1].sources && messages[messages.length - 1].sources!.length > 0 && (
          <div className="border-t border-white/5 bg-black/30 backdrop-blur">
            <Button variant="ghost" className="w-full justify-between p-3 md:p-4 hover:bg-white/5 rounded-none" onClick={() => setShowSources(!showSources)}>
              <span className="font-semibold text-sm md:text-base">Sources ({messages[messages.length - 1].sources!.length})</span>
              {showSources ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </Button>
            {showSources && (
              <div className="px-3 md:px-6 pb-5 space-y-3">
                {messages[messages.length - 1].sources!.map((source, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 rounded-2xl border border-white/10 bg-white/5">
                    <div className="flex-shrink-0 w-7 h-7 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-semibold">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium hover:underline flex items-center gap-1">
                        {source.title}
                        <ExternalLink className="w-3 h-3 flex-shrink-0" />
                      </a>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{source.excerpt}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline" className="text-xs">
                          {source.category}
                        </Badge>
                        <span className="text-xs text-muted-foreground truncate">{source.source_name}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="border-t border-white/5 bg-background/80 p-3 md:p-6">
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <div className="flex items-center gap-2">
                <Sparkles className="w-3.5 h-3.5 text-primary" />
                {isResearchMode
                  ? "Deep research mode prioritizes structure & citations."
                  : "Chat mode delivers fast summaries with citations."}
              </div>
              <span>{isLoading ? "Streaming..." : "Ready"}</span>
            </div>
            <div className="rounded-[28px] border border-white/10 bg-white/5 px-4 py-3 shadow-lg backdrop-blur-lg">
              <div className="flex items-end gap-3">
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="icon" type="button" className="h-10 w-10 rounded-2xl text-muted-foreground">
                    <Paperclip className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="icon" type="button" className="h-10 w-10 rounded-2xl text-muted-foreground">
                    <Mic className="w-4 h-4" />
                  </Button>
                </div>
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={
                    isResearchMode
                      ? "Ask detailed legal research questions about Kenyan laws..."
                      : "Ask about Kenyan law, parliament, or news..."
                  }
                  className="flex-1 border-0 bg-transparent text-sm md:text-base focus-visible:ring-0"
                  disabled={isLoading}
                />
                <Button type="submit" disabled={isLoading || !input.trim()} className="h-12 w-12 rounded-2xl">
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </Button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}