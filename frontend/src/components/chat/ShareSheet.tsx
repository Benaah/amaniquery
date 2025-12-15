import React from "react"
import { Button } from "@/components/ui/button"
import { Loader2, X, Copy, ImageIcon, ExternalLink, LogIn, Link2 } from "lucide-react"
import type { Message, SharePlatform, ShareSheetState } from "./types"
import { SHARE_PLATFORMS } from "./constants"
import { motion, AnimatePresence } from "framer-motion"

interface ShareSheetProps {
  message: Message
  shareSheet: ShareSheetState
  onClose: () => void
  onChangePlatform: (message: Message, platform: SharePlatform) => void
  onCopyContent: () => void
  onGenerateImage: (message: Message) => void
  onOpenIntent: (message: Message) => void
  onAuthenticate: (platform: SharePlatform) => void
  onPostDirectly: (message: Message) => void
  platformTokens: Record<SharePlatform, string | null>
}

export function ShareSheet({
  message,
  shareSheet,
  onClose,
  onChangePlatform,
  onCopyContent,
  onGenerateImage,
  onOpenIntent,
  onAuthenticate,
  onPostDirectly,
  platformTokens
}: ShareSheetProps) {
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 10, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 10, scale: 0.98 }}
        className="rounded-3xl border border-white/10 bg-background/80 backdrop-blur-xl p-3 md:p-5 space-y-3 md:space-y-4 mt-2 shadow-2xl"
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-primary/80 font-semibold">Social Share</p>
            <h4 className="font-semibold text-sm">Turn this answer into a post</h4>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full hover:bg-white/10" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {SHARE_PLATFORMS.map((platform) => (
            <button
              type="button"
              key={platform.id}
              onClick={() => onChangePlatform(message, platform.id)}
              className={`group relative overflow-hidden rounded-2xl border p-2.5 md:p-3 text-left transition-all duration-200 min-h-[60px] ${
                shareSheet.platform === platform.id 
                  ? "border-primary/50 bg-primary/5 ring-1 ring-primary/20" 
                  : "border-white/10 bg-white/[0.04] hover:border-white/20 hover:bg-white/10"
              }`}
            >
              <div className={`inline-flex items-center gap-2 rounded-full bg-gradient-to-r ${platform.accent} px-2.5 py-1 text-[11px] font-semibold shadow-sm`}>
                {platform.icon}
                {platform.label}
              </div>
              <p className="mt-2 text-[10px] md:text-[11px] text-muted-foreground font-medium">{platform.description}</p>
              
              {shareSheet.platform === platform.id && (
                  <motion.div 
                    layoutId="active-platform"
                    className="absolute inset-0 rounded-2xl pointer-events-none border-2 border-primary/20"
                    initial={false}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
              )}
            </button>
          ))}
        </div>

        <div className="rounded-2xl border border-white/10 bg-black/20 p-4 min-h-[120px]">
          {shareSheet.isLoading ? (
            <div className="flex flex-col items-center justify-center h-24 gap-2 text-sm text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin text-primary" />
              <p>Formatting for {SHARE_PLATFORMS.find(p => p.id === shareSheet.platform)?.label}...</p>
            </div>
          ) : shareSheet.preview ? (
            <motion.div 
                initial={{ opacity: 0 }} 
                animate={{ opacity: 1 }} 
                className="space-y-3"
            >
              <div className="flex items-center justify-between">
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Preview</p>
                {shareSheet.preview.character_count && (
                    <span className="text-[10px] text-muted-foreground">{shareSheet.preview.character_count} chars</span>
                )}
              </div>
              
              <div className="rounded-xl bg-background/50 border border-white/5 p-3 max-h-64 overflow-auto text-xs md:text-sm whitespace-pre-wrap [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] font-medium leading-relaxed">
                {Array.isArray(shareSheet.preview.content)
                  ? shareSheet.preview.content.join("\n\n")
                  : shareSheet.preview.content}
              </div>
              
              {shareSheet.preview.hashtags && shareSheet.preview.hashtags.length > 0 && (
                <div className="flex flex-wrap gap-2 text-[11px] text-primary">
                  {shareSheet.preview.hashtags.map((tag) => (
                    <span key={tag} className="rounded-full bg-primary/10 border border-primary/10 px-2 py-0.5">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </motion.div>
          ) : null}
          
          {shareSheet.shareError && (
             <motion.p initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="mt-3 text-xs text-red-400 bg-red-500/10 p-2 rounded-lg border border-red-500/20">
                {shareSheet.shareError}
             </motion.p>
          )}
          {shareSheet.success && (
              <motion.p initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="mt-3 text-xs text-emerald-400 bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/20">
                {shareSheet.success}
              </motion.p>
          )}
        </div>

        <div className="flex flex-wrap gap-2 pt-1 border-t border-white/5">
          <Button 
            variant="outline" 
            size="sm" 
            className="rounded-full border-white/10 bg-white/5 hover:bg-white/10 text-xs min-h-[40px] px-4 flex-1"
            onClick={onCopyContent} 
            disabled={!shareSheet.preview}
          >
            <Copy className="w-3.5 h-3.5 mr-2" />
            Copy text
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            className="rounded-full border-white/10 bg-white/5 hover:bg-white/10 text-xs min-h-[40px] px-4 flex-1"
            onClick={() => onGenerateImage(message)}
            disabled={!shareSheet.preview || shareSheet.generatingImage}
          >
            {shareSheet.generatingImage ? <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" /> : <ImageIcon className="w-3.5 h-3.5 mr-2" />}
            Image
          </Button>
          
          <Button
            variant="default"
            size="sm"
            className="rounded-full text-xs min-h-[40px] px-4 flex-1 bg-primary hover:bg-primary/90"
            onClick={() => onOpenIntent(message)}
            disabled={!shareSheet.preview || shareSheet.shareLinkLoading}
          >
            {shareSheet.shareLinkLoading ? <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" /> : <ExternalLink className="w-3.5 h-3.5 mr-2" />}
            Share
          </Button>

          {/* Conditional buttons for Auth and Direct Posting */}
          {!platformTokens[shareSheet.platform] && (
            <Button
              variant="outline"
              size="sm"
              className="rounded-full border-orange-500/30 bg-orange-500/5 text-orange-400 hover:bg-orange-500/10 text-xs min-h-[40px] px-3"
              onClick={() => onAuthenticate(shareSheet.platform)}
              disabled={shareSheet.shareLinkLoading}
              title="Authenticate to post directly"
            >
               {shareSheet.shareLinkLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <LogIn className="w-3.5 h-3.5" />}
            </Button>
          )}
          
          <Button
            variant="ghost"
            size="sm"
            className="rounded-full text-xs min-h-[40px] px-3 text-muted-foreground hover:text-primary"
            onClick={() => onPostDirectly(message)}
            disabled={!shareSheet.preview || shareSheet.posting || !platformTokens[shareSheet.platform]}
            title="Post directly (Beta)"
          >
            {shareSheet.posting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Link2 className="w-3.5 h-3.5" />}
          </Button>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
