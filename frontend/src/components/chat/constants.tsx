import { Twitter, Linkedin, Facebook } from "lucide-react"
import type { SharePlatformConfig } from "./types"

export const SHARE_PLATFORMS: SharePlatformConfig[] = [
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
