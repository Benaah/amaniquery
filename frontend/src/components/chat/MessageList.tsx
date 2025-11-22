import { useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import {
  Bot,
  User,
  Loader2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Eye,
  Image as ImageIcon,
  FileText,
  Edit,
  Copy,
  RotateCw,
  ThumbsUp,
  ThumbsDown,
  Share2,
  Search,
  Download,
  X,
  Link2,
  Check
} from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeRaw from "rehype-raw"
import rehypeHighlight from "rehype-highlight"
import { WelcomeScreen } from "./WelcomeScreen"
import { ImagePreview } from "./ImagePreview"
import { SHARE_PLATFORMS } from "./constants"
import type { Message, Source, SharePlatform, ShareSheetState } from "./types"

interface MessageListProps {
  messages: Message[]
  isLoading: boolean
  isResearchMode: boolean
  useHybrid: boolean
  onSendMessage: (content: string) => void
  onRegenerate: (messageId: string) => void
  onFeedback: (messageId: string, type: "like" | "dislike") => void
  onCopy: (content: string) => void
  onShare: (message: Message) => void
  onGeneratePDF: (messageId: string) => void
  onGenerateWord: (messageId: string) => void
  showSources: boolean
  onToggleSources: () => void
  messagesContainerRef: React.RefObject<HTMLDivElement | null>
  messagesEndRef: React.RefObject<HTMLDivElement | null>
  editingMessageId: string | null
  editingContent: string
  setEditingContent: (content: string) => void
  onSaveEdit: (messageId: string) => void
  onCancelEdit: () => void
  onStartEdit: (message: Message) => void
  regeneratingMessageId: string | null
  shareSheet: ShareSheetState | null
  onCloseShareSheet: () => void
  onChangeSharePlatform: (message: Message, platform: SharePlatform) => void
  onCopyShareContent: () => void
  onOpenShareIntent: (message: Message) => void
  onPostDirectly: (message: Message) => void
  onCopyFailedQuery: (message: Message) => void
  onEditFailedQuery: (message: Message) => void
  onResendFailedQuery: (message: Message) => void
}

export function MessageList({
  messages,
  isLoading,
  isResearchMode,
  useHybrid,
  onSendMessage,
  onRegenerate,
  onFeedback,
  onCopy,
  onShare,
  onGeneratePDF,
  onGenerateWord,
  showSources,
  onToggleSources,
  messagesContainerRef,
  messagesEndRef,
  editingMessageId,
  editingContent,
  setEditingContent,
  onSaveEdit,
  onCancelEdit,
  onStartEdit,
  regeneratingMessageId,
  shareSheet,
  onCloseShareSheet,
  onChangeSharePlatform,
  onCopyShareContent,
  onOpenShareIntent,
  onPostDirectly,
  onCopyFailedQuery,
  onEditFailedQuery,
  onResendFailedQuery
}: MessageListProps) {

  const formatTimestamp = (dateString: string) => {
    const date = new Date(dateString)
    if (Number.isNaN(date.getTime())) return ""
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
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
    <div className="flex-1 overflow-hidden flex flex-col min-h-0">
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-3 md:px-8 py-6 space-y-4 min-h-0 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
      >
        {messages.length === 0 && (
          <WelcomeScreen
            isResearchMode={isResearchMode}
            useHybrid={useHybrid}
            onSuggestionClick={onSendMessage}
          />
        )}

        {messages.map((message, index) => {
          const prevMessage = index > 0 ? messages[index - 1] : null
          const showDateSeparator = !prevMessage || 
            new Date(message.created_at).toDateString() !== new Date(prevMessage.created_at).toDateString()
          const showAvatar = !prevMessage || prevMessage.role !== message.role || 
            (new Date(message.created_at).getTime() - new Date(prevMessage.created_at).getTime()) > 300000 // 5 minutes
          
          return (
            <div key={message.id}>
              {showDateSeparator && (
                <div className="flex items-center justify-center my-6">
                  <div className="text-xs text-muted-foreground bg-background/80 px-4 py-1.5 rounded-full border border-white/10">
                    {new Date(message.created_at).toLocaleDateString(undefined, { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </div>
                </div>
              )}
              <div
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} group animate-in fade-in slide-in-from-bottom-2 duration-300`}
              >
                <div
                  className={`flex w-full max-w-3xl ${message.role === "user" ? "flex-row-reverse text-right" : "flex-row"} gap-3`}
                >
                  {showAvatar && (
                    <div
                      className={`flex-shrink-0 h-10 w-10 rounded-2xl border border-white/10 backdrop-blur flex items-center justify-center transition-all duration-200 ${
                        message.role === "user" ? "bg-primary/90 text-primary-foreground" : "bg-white/5 text-white"
                      }`}
                    >
                      {message.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>
                  )}
                  {!showAvatar && <div className="flex-shrink-0 w-10" />}
                  <div className="flex-1 space-y-3">
                    {editingMessageId === message.id && message.role === "user" ? (
                      <Card className="rounded-3xl border border-primary/50 bg-primary/10 backdrop-blur-xl">
                        <CardContent className="p-4 md:p-6 space-y-3">
                          <Textarea
                            value={editingContent}
                            onChange={(e) => setEditingContent(e.target.value)}
                            className="w-full min-h-[100px] bg-background/50 border-white/20"
                            onKeyDown={(e) => {
                              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                                e.preventDefault()
                                onSaveEdit(message.id)
                              }
                              if (e.key === "Escape") {
                                onCancelEdit()
                              }
                            }}
                            autoFocus
                          />
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              onClick={() => onSaveEdit(message.id)}
                              className="h-8 rounded-full"
                            >
                              <Check className="w-4 h-4 mr-1" />
                              Save
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={onCancelEdit}
                              className="h-8 rounded-full"
                            >
                              <X className="w-4 h-4 mr-1" />
                              Cancel
                            </Button>
                            <span className="text-xs text-muted-foreground ml-auto">
                              Press Cmd/Ctrl+Enter to save, Esc to cancel
                            </span>
                          </div>
                        </CardContent>
                      </Card>
                    ) : (
                      <Card
                        className={`rounded-3xl border border-white/5 bg-white/5 text-sm md:text-base shadow-xl transition-all duration-200 ${
                          message.role === "user" 
                            ? "bg-primary text-primary-foreground dark:bg-primary/90 dark:text-primary-foreground" 
                            : "backdrop-blur-xl"
                        } ${message.failed ? "border-red-500/50 bg-red-500/10" : ""} ${
                          regeneratingMessageId === message.id ? "animate-pulse" : ""
                        }`}
                      >
                        <CardContent className="p-4 md:p-6 space-y-3">
                        <div className={`flex flex-wrap items-center gap-2 text-xs uppercase tracking-wider ${
                          message.role === "user" 
                            ? "text-primary-foreground/80 dark:text-primary-foreground/80" 
                            : "text-muted-foreground"
                        }`}>
                          <span>{message.role === "user" ? "You" : "AmaniQuery"}</span>
                          <span className="h-1 w-1 rounded-full bg-muted-foreground/50" />
                          <span>{formatTimestamp(message.created_at)}</span>
                          {message.failed && (
                            <>
                              <span className="h-1 w-1 rounded-full bg-red-500/50" />
                              <span className="text-red-400">Failed</span>
                            </>
                          )}
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

                        {message.model_used === "gemini-2.5-flash" && message.sources && 
                         message.sources.some((src: Source) => src.category === "vision") && (
                          <div className="inline-flex items-center gap-2 rounded-full border border-purple-500/40 bg-purple-500/10 px-3 py-1 text-xs text-purple-100">
                            <Eye className="w-3.5 h-3.5" />
                            Vision RAG Analysis
                          </div>
                        )}

                        {/* Attachments - displayed above message content */}
                        {message.attachments && message.attachments.length > 0 && (
                          <div className="space-y-3">
                            {/* Separate images from other files */}
                            {message.attachments.filter(att => {
                              const isImage = att.file_type === "image" || 
                                /\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(att.filename)
                              return isImage && att.cloudinary_url
                            }).length > 0 && (
                              <div className="space-y-2">
                                {message.attachments
                                  .filter(att => {
                                    const isImage = att.file_type === "image" || 
                                      /\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(att.filename)
                                    return isImage && att.cloudinary_url
                                  })
                                  .map((attachment) => (
                                    <ImagePreview
                                      key={attachment.id}
                                      src={attachment.cloudinary_url!}
                                      alt={attachment.filename}
                                      className="w-full"
                                    />
                                  ))}
                              </div>
                            )}

                            {/* Non-image files and images without Cloudinary URLs */}
                            {message.attachments
                              .filter(att => {
                                const isImage = att.file_type === "image" || 
                                  /\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(att.filename)
                                return !isImage || !att.cloudinary_url
                              })
                              .map((attachment) => {
                                const isImage = attachment.file_type === "image" || 
                                  /\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(attachment.filename)
                                const isPDF = attachment.file_type === "pdf" || 
                                  attachment.filename.toLowerCase().endsWith(".pdf")
                                
                                return (
                                  <div
                                    key={attachment.id}
                                    className="flex items-start gap-2 p-2 rounded-lg border border-white/10 bg-white/5"
                                  >
                                    {isImage ? (
                                      <ImageIcon className="w-4 h-4 text-muted-foreground mt-1" />
                                    ) : isPDF ? (
                                      <FileText className="w-4 h-4 text-muted-foreground mt-1" />
                                    ) : (
                                      <FileText className="w-4 h-4 text-muted-foreground mt-1" />
                                    )}
                                    <div className="flex-1 min-w-0">
                                      <p className="text-sm font-medium truncate">{attachment.filename}</p>
                                      <p className="text-xs text-muted-foreground">
                                        {(attachment.file_size / 1024).toFixed(1)} KB • {attachment.file_type}
                                      </p>
                                      {isImage && !attachment.cloudinary_url && (
                                        <p className="text-xs text-blue-400 mt-1">
                                          📷 Ready for Vision RAG analysis
                                        </p>
                                      )}
                                      {isPDF && (
                                        <p className="text-xs text-blue-400 mt-1">
                                          📄 Pages will be analyzed with Vision RAG
                                        </p>
                                      )}
                                    </div>
                                    {attachment.processed && (
                                      <Badge variant="outline" className="text-xs">
                                        Processed
                                      </Badge>
                                    )}
                                  </div>
                                )
                              })}
                          </div>
                        )}

                        <div className={`prose prose-sm md:prose-base max-w-none dark:prose-invert text-sm md:text-base ${
                          message.role === "user" 
                            ? "prose-headings:text-primary-foreground prose-p:text-primary-foreground prose-strong:text-primary-foreground prose-em:text-primary-foreground prose-code:text-primary-foreground prose-pre:text-primary-foreground prose-a:text-primary-foreground/90 hover:prose-a:text-primary-foreground prose-li:text-primary-foreground" 
                            : ""
                        }`}>
                          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw, rehypeHighlight]}>
                            {formatMessageWithCitations(message.content, message.sources)}
                          </ReactMarkdown>
                        </div>
                      </CardContent>
                    </Card>
                    )}

                    {message.role === "user" && !message.failed && editingMessageId !== message.id && (
                      <div className="flex flex-wrap items-center gap-2 justify-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onStartEdit(message)}
                          className="h-9 rounded-full px-3 text-xs text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Edit className="w-4 h-4 mr-1" />
                          Edit
                        </Button>
                      </div>
                    )}

                    {message.failed && (
                      <div className="flex flex-wrap items-center gap-2 justify-start">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onCopyFailedQuery(message)}
                          className="h-9 rounded-full px-3 text-xs border-red-500/50 text-red-400 hover:bg-red-500/10"
                        >
                          <Copy className="w-4 h-4 mr-1" />
                          Copy Query
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onEditFailedQuery(message)}
                          className="h-9 rounded-full px-3 text-xs border-red-500/50 text-red-400 hover:bg-red-500/10"
                        >
                          <Edit className="w-4 h-4 mr-1" />
                          Edit
                        </Button>
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => onResendFailedQuery(message)}
                          disabled={isLoading}
                          className="h-9 rounded-full px-3 text-xs bg-red-600 hover:bg-red-700 text-white"
                        >
                          <RotateCw className="w-4 h-4 mr-1" />
                          Retry
                        </Button>
                      </div>
                    )}

                    {message.role === "assistant" && !message.failed && (
                      <div className="flex flex-wrap items-center gap-2 justify-start">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onRegenerate(message.id)}
                          disabled={!message.saved || isLoading || regeneratingMessageId === message.id}
                          className="h-9 rounded-full px-3 text-xs text-muted-foreground hover:text-primary"
                        >
                          {regeneratingMessageId === message.id ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                              Regenerating...
                            </>
                          ) : (
                            <>
                              <RotateCw className="w-4 h-4 mr-1" />
                              Regenerate
                            </>
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onFeedback(message.id, "like")}
                          disabled={!message.saved}
                          className={`h-9 rounded-full px-3 text-xs ${message.feedback_type === "like" ? "text-green-500" : "text-muted-foreground"}`}
                        >
                          <ThumbsUp className="w-4 h-4 mr-1" />
                          Helpful
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onFeedback(message.id, "dislike")}
                          disabled={!message.saved}
                          className={`h-9 rounded-full px-3 text-xs ${message.feedback_type === "dislike" ? "text-red-500" : "text-muted-foreground"}`}
                        >
                          <ThumbsDown className="w-4 h-4 mr-1" />
                          Refine
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onCopy(message.content)}
                          className="h-9 rounded-full px-3 text-xs text-muted-foreground"
                        >
                          <Copy className="w-4 h-4 mr-1" />
                          Copy
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onShare(message)}
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
                              onClick={() => onGeneratePDF(message.id)}
                              disabled={!message.saved}
                              className="h-9 rounded-full px-3 text-xs text-muted-foreground"
                            >
                              <FileText className="w-4 h-4 mr-1" />
                              PDF
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onGenerateWord(message.id)}
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
                          <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full" onClick={onCloseShareSheet}>
                            <X className="w-4 h-4" />
                          </Button>
                        </div>

                        <div className="grid gap-2 md:grid-cols-3">
                          {SHARE_PLATFORMS.map((platform) => (
                            <button
                              type="button"
                              key={platform.id}
                              onClick={() => onChangeSharePlatform(message, platform.id)}
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
                              <div className="rounded-xl bg-background/80 border border-white/10 p-3 max-h-64 overflow-auto text-xs md:text-sm whitespace-pre-wrap [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
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
                          <Button variant="outline" size="sm" className="rounded-full border-white/20 text-xs" onClick={onCopyShareContent} disabled={!shareSheet.preview}>
                            <Copy className="w-4 h-4 mr-1" />
                            Copy text
                          </Button>
                          <Button
                            variant="default"
                            size="sm"
                            className="rounded-full text-xs"
                            onClick={() => onOpenShareIntent(message)}
                            disabled={!shareSheet.preview || shareSheet.shareLinkLoading}
                          >
                            {shareSheet.shareLinkLoading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <ExternalLink className="w-4 h-4 mr-1" />}
                            Open share dialog
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="rounded-full text-xs"
                            onClick={() => onPostDirectly(message)}
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
            </div>
          )
        })}

        {isLoading && (
          <div className="flex justify-start animate-in fade-in slide-in-from-bottom-2">
            <div className="flex w-full max-w-3xl items-start gap-3">
              <div className="flex-shrink-0 h-10 w-10 rounded-2xl border border-white/10 bg-white/5 flex items-center justify-center animate-pulse">
                <Bot className="w-4 h-4 text-primary" />
              </div>
              <Card className="rounded-3xl border border-white/5 bg-white/5 px-5 py-4 backdrop-blur-xl">
                <div className="flex items-center gap-3 text-sm text-muted-foreground">
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  <div className="flex items-center gap-1">
                    <span className="animate-pulse">Thinking</span>
                    <span className="animate-bounce delay-75">.</span>
                    <span className="animate-bounce delay-150">.</span>
                    <span className="animate-bounce delay-300">.</span>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {messages.length > 0 && messages[messages.length - 1].sources && messages[messages.length - 1].sources!.length > 0 && (
        <div className="border-t border-white/5 bg-black/30 backdrop-blur flex-shrink-0">
          <Button variant="ghost" className="w-full justify-between p-3 md:p-4 hover:bg-white/5 rounded-none" onClick={onToggleSources}>
            <span className="font-semibold text-sm md:text-base">Sources ({messages[messages.length - 1].sources!.length})</span>
            {showSources ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
          {showSources && (
            <div className="px-3 md:px-6 pb-5 space-y-3">
              {messages[messages.length - 1].sources!.map((source, index) => {
                const isVisionSource = source.category === "vision"
                return (
                  <div key={index} className="flex items-start space-x-3 p-3 rounded-2xl border border-white/10 bg-white/5">
                    <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${
                      isVisionSource 
                        ? "bg-purple-500/20 text-purple-300 border border-purple-500/40" 
                        : "bg-primary text-primary-foreground"
                    }`}>
                      {isVisionSource ? <ImageIcon className="w-4 h-4" /> : index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      {source.url ? (
                        <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium hover:underline flex items-center gap-1">
                          {source.title}
                          <ExternalLink className="w-3 h-3 flex-shrink-0" />
                        </a>
                      ) : (
                        <div className="text-sm font-medium flex items-center gap-1">
                          {isVisionSource && <Eye className="w-3 h-3 text-purple-400" />}
                          {source.title}
                        </div>
                      )}
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{source.excerpt}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline" className={`text-xs ${
                          isVisionSource ? "border-purple-500/40 text-purple-300" : ""
                        }`}>
                          {isVisionSource ? "🖼️ Vision" : source.category}
                        </Badge>
                        <span className="text-xs text-muted-foreground truncate">{source.source_name}</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
