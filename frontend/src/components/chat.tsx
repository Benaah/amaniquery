"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { 
  Send, Bot, User, Settings, ThumbsUp, ThumbsDown, 
  Copy, Share2, History, MessageSquare, Plus, ChevronDown, ChevronUp, ExternalLink, Trash2, Search,
  FileText, Download
} from "lucide-react"
import { toast } from "sonner"

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

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

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
      created_at: new Date().toISOString()
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
            model_used: data.model_used || "gemini-research"
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
            model_used: "streaming"
          }
          
          // Add initial empty assistant message
          setMessages(prev => [...prev, assistantMessage])
          
          const reader = response.body?.getReader()
          const decoder = new TextDecoder()
          let accumulatedContent = ""
          let metadata: StreamMetadata = {}
          
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
                      
                      if (parsed.content) {
                        accumulatedContent += parsed.content
                        // Update message content in real-time
                        setMessages(prev => prev.map(msg => 
                          msg.id === assistantMessageId 
                            ? { ...msg, content: accumulatedContent }
                            : msg
                        ))
                      }
                      
                      if (parsed.metadata) {
                        metadata = { ...metadata, ...parsed.metadata }
                      }
                      
                      if (parsed.done) {
                        // Final update with metadata
                        setMessages(prev => prev.map(msg => 
                          msg.id === assistantMessageId 
                            ? { 
                                ...msg, 
                                content: accumulatedContent,
                                token_count: metadata.token_count,
                                model_used: metadata.model_used,
                                sources: metadata.sources
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

  const shareChat = async () => {
    if (!currentSessionId) return
    
    try {
      const response = await fetch(`${API_BASE_URL}/chat/share?session_id=${encodeURIComponent(currentSessionId)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      })
      if (response.ok) {
        const data = await response.json()
        await navigator.clipboard.writeText(`${window.location.origin}${data.share_link}`)
        toast.success("Share link copied to clipboard!")
      } else {
        console.error("Failed to generate share link:", response.status)
        toast.error("Failed to generate share link")
      }
    } catch (error) {
      console.error("Failed to generate share link:", error)
      toast.error("Failed to generate share link")
    }
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

  const suggestedQuestions = [
    "What are the latest developments in Kenyan constitutional law?",
    "Can you explain the recent changes to the Kenyan Penal Code?",
    "What are the key provisions of the Kenyan Competition Act?",
    "How does the Kenyan judiciary handle environmental law cases?",
    "What are the requirements for starting a business in Kenya?"
  ]

  const researchSuggestedQuestions = [
    "Conduct a comprehensive analysis of the Kenyan Constitution's Bill of Rights and its implications for digital rights",
    "Research the evolution of environmental law in Kenya and its effectiveness in conservation efforts",
    "Analyze the impact of recent amendments to the Kenyan Penal Code on cybercrime legislation",
    "Investigate the constitutional framework for devolution in Kenya and its implementation challenges",
    "Examine the legal framework governing data protection and privacy rights in Kenya"
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
    <div className="flex h-screen max-w-6xl mx-auto">
      {/* Chat History Sidebar - Desktop */}
      <div className="hidden md:flex w-80 border-r bg-muted/30 overflow-y-auto flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Chat History</h3>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={createNewSession}
            >
              <Plus className="w-4 h-4 mr-2" />
              New Chat
            </Button>
          </div>
        </div>
        <div className="p-2 space-y-1 flex-1">
          {chatHistory.map((session) => (
            <div key={session.id} className="flex items-center space-x-2 p-1">
              <Button
                variant={currentSessionId === session.id ? "secondary" : "ghost"}
                className="flex-1 justify-start text-left h-auto p-3"
                onClick={() => loadSession(session.id)}
              >
                <MessageSquare className="w-4 h-4 mr-2 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">
                    {session.title || `Chat ${session.id.slice(-8)}`}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {session.message_count} messages
                  </div>
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

      {/* Mobile Sidebar Overlay */}
      {showHistory && (
        <div className="md:hidden fixed inset-0 z-50 bg-black/50" onClick={() => setShowHistory(false)}>
          <div className="absolute left-0 top-0 h-full w-80 bg-background border-r shadow-lg" onClick={(e) => e.stopPropagation()}>
            <div className="p-4 border-b">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Chat History</h3>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => setShowHistory(false)}
                >
                  ×
                </Button>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full mt-2"
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
                      <div className="font-medium truncate">
                        {session.title || `Chat ${session.id.slice(-8)}`}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {session.message_count} messages
                      </div>
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

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-2">
            <Button 
              variant="ghost" 
              size="sm"
              className="md:hidden"
              onClick={() => setShowHistory(!showHistory)}
            >
              <History className="w-4 h-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="sm"
              className="hidden md:inline-flex"
              onClick={() => setShowHistory(!showHistory)}
            >
              <History className="w-4 h-4" />
            </Button>
            <h1 className="text-xl md:text-2xl font-bold">AmaniQuery</h1>
            {isResearchMode && (
              <Badge variant="default" className="bg-blue-600">
                <Search className="w-3 h-3 mr-1" />
                Research Mode
              </Badge>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <Button 
              variant={isResearchMode ? "default" : "outline"} 
              size="sm"
              onClick={() => setIsResearchMode(!isResearchMode)}
              className={`${isResearchMode ? "bg-blue-600 hover:bg-blue-700" : ""} h-9 px-3`}
            >
              <Search className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Research Mode</span>
              <span className="sm:hidden">Research</span>
            </Button>
            <Badge variant="secondary" className="hidden sm:inline-flex">RAG-Powered Legal & News Intelligence</Badge>
            <Badge variant="secondary" className="sm:hidden">RAG AI</Badge>
            {currentSessionId && (
              <Button variant="outline" size="sm" className="h-9 px-3">
                <Share2 className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Share</span>
              </Button>
            )}
            <Link href="/">
              <Button variant="outline" size="sm" className="h-9 px-3">
                <Settings className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Home</span>
              </Button>
            </Link>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-2 md:p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-8 md:py-12">
              <Bot className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h2 className="text-lg md:text-xl font-semibold mb-2">
                Welcome to AmaniQuery {isResearchMode && "- Research Mode"}
              </h2>
              <p className="text-muted-foreground mb-6 px-4 text-sm md:text-base">
                {isResearchMode 
                  ? "Ask detailed legal research questions about Kenyan laws. Get comprehensive analysis with sources and recommendations."
                  : "Ask questions about Kenyan law, parliament, and news. Get factual answers with verifiable sources."
                }
              </p>
              <div className="flex flex-col gap-3 md:gap-4 max-w-2xl mx-auto px-4">
                {(isResearchMode ? researchSuggestedQuestions : suggestedQuestions).map((question, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    className="text-left justify-start h-auto p-3 md:p-4 whitespace-normal text-sm md:text-base"
                    onClick={() => sendMessage(question)}
                  >
                    {question}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex max-w-[90%] md:max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.role === 'user' ? 'bg-primary text-primary-foreground ml-2' : 'bg-muted mr-2'
                }`}>
                  {message.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                <div className="flex-1">
                  <Card className={`max-w-full ${message.role === 'user' ? 'bg-primary text-primary-foreground' : ''}`}>
                    <CardContent className="p-3 md:p-4">
                      {message.model_used === 'gemini-research' && (
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="secondary" className="text-xs">
                            <Search className="w-3 h-3 mr-1" />
                            Legal Research
                          </Badge>
                        </div>
                      )}
                      <div
                        className="prose prose-sm max-w-none dark:prose-invert text-sm md:text-base"
                        dangerouslySetInnerHTML={{
                          __html: formatMessageWithCitations(message.content, message.sources)
                        }}
                      />
                    </CardContent>
                  </Card>
                  
                  {/* Message Actions */}
                  {message.role === 'assistant' && message.model_used !== 'gemini-research' && (
                    <div className="flex items-center space-x-1 md:space-x-2 mt-2 ml-10">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => submitFeedback(message.id, 'like')}
                        className={`h-8 w-8 p-0 ${message.feedback_type === 'like' ? 'text-green-600' : ''}`}
                      >
                        <ThumbsUp className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => submitFeedback(message.id, 'dislike')}
                        className={`h-8 w-8 p-0 ${message.feedback_type === 'dislike' ? 'text-red-600' : ''}`}
                      >
                        <ThumbsDown className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(message.content)}
                        className="h-8 w-8 p-0"
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                  {message.role === 'assistant' && message.model_used === 'gemini-research' && (
                    <div className="flex items-center space-x-1 md:space-x-2 mt-2 ml-10">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => generatePDF(message.id)}
                        title="Download as PDF"
                        className="h-8 px-2 text-xs"
                      >
                        <FileText className="w-4 h-4 mr-1" />
                        PDF
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => generateWord(message.id)}
                        title="Download as Word"
                        className="h-8 px-2 text-xs"
                      >
                        <Download className="w-4 h-4 mr-1" />
                        Word
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(message.content)}
                        className="h-8 w-8 p-0"
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="flex max-w-[90%] md:max-w-[80%]">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center mr-2">
                  <Bot className="w-4 h-4" />
                </div>
                <Card>
                  <CardContent className="p-3 md:p-4">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </div>

        {/* Sources */}
        {messages.length > 0 && messages[messages.length - 1].sources && messages[messages.length - 1].sources!.length > 0 && (
          <div className="border-t bg-muted/50">
            <Button
              variant="ghost"
              className="w-full justify-between p-3 md:p-4 hover:bg-muted/70"
              onClick={() => setShowSources(!showSources)}
            >
              <span className="font-semibold text-sm md:text-base">Sources ({messages[messages.length - 1].sources!.length})</span>
              {showSources ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </Button>
            {showSources && (
              <div className="px-3 md:px-4 pb-3 md:pb-4 space-y-3">
                {messages[messages.length - 1].sources!.map((source, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-background rounded-lg border">
                    <div className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-semibold">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium hover:underline flex items-center gap-1"
                      >
                        {source.title}
                        <ExternalLink className="w-3 h-3 flex-shrink-0" />
                      </a>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{source.excerpt}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline" className="text-xs">{source.category}</Badge>
                        <span className="text-xs text-muted-foreground truncate">{source.source_name}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Input */}
        <div className="border-t p-3 md:p-4">
          <form onSubmit={handleSubmit} className="flex space-x-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                isResearchMode 
                  ? "Ask detailed legal research questions about Kenyan laws..."
                  : "Ask about Kenyan law, parliament, or news..."
              }
              className="flex-1 h-10 md:h-11 text-sm md:text-base"
              disabled={isLoading}
            />
            <Button type="submit" disabled={isLoading || !input.trim()} className="h-10 md:h-11 px-3 md:px-4">
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}