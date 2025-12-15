import { Twitter, Linkedin, Facebook, MessageCircle, Send, Mail, AtSign, Cloud, Video } from "lucide-react"
import type { SharePlatformConfig } from "./types"

export const SHARE_PLATFORMS: SharePlatformConfig[] = [
  {
    id: "twitter",
    label: "X",
    accent: "from-[#000000] to-[#1a1a1a] text-white",
    description: "280 characters",
    icon: <Twitter className="w-4 h-4" />
  },
  {
    id: "whatsapp",
    label: "WhatsApp",
    accent: "from-[#25D366] to-[#1EBE57] text-white",
    description: "Share via chat",
    icon: <MessageCircle className="w-4 h-4" />
  },
  {
    id: "linkedin",
    label: "LinkedIn",
    accent: "from-[#0A66C2] to-[#004182] text-white",
    description: "Professional",
    icon: <Linkedin className="w-4 h-4" />
  },
  {
    id: "telegram",
    label: "Telegram",
    accent: "from-[#0088cc] to-[#006699] text-white",
    description: "Instant messaging",
    icon: <Send className="w-4 h-4" />
  },
  {
    id: "facebook",
    label: "Facebook",
    accent: "from-[#1877F2] to-[#0F5EC7] text-white",
    description: "Social network",
    icon: <Facebook className="w-4 h-4" />
  },
  {
    id: "email",
    label: "Email",
    accent: "from-[#EA4335] to-[#C5221F] text-white",
    description: "Send via email",
    icon: <Mail className="w-4 h-4" />
  },
  {
    id: "threads",
    label: "Threads",
    accent: "from-[#000000] to-[#1a1a1a] text-white",
    description: "500 characters",
    icon: <AtSign className="w-4 h-4" />
  },
  {
    id: "bluesky",
    label: "Bluesky",
    accent: "from-[#0085ff] to-[#0062bd] text-white",
    description: "300 characters",
    icon: <Cloud className="w-4 h-4" />
  },
  {
    id: "tiktok",
    label: "TikTok",
    accent: "from-[#000000] to-[#1a1a1a] text-white",
    description: "2200 characters",
    icon: <Video className="w-4 h-4" />
  }
]

export interface SuggestionTile {
  title: string
  description: string
}

export const SUGGESTED_QUESTIONS: SuggestionTile[] = [
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

export const RESEARCH_SUGGESTED_QUESTIONS: SuggestionTile[] = [
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
