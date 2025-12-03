import type { ReactNode } from "react"
import type { AmaniQueryResponse as StructuredResponse } from "../AmaniQueryResponse"

export type { StructuredResponse }

export interface WidgetInput {
    name: string
    label: string
    type: string
    placeholder?: string
    default_value?: string
}

export interface WidgetOutput {
    label: string
    format: string
}

export interface InteractiveWidget {
    type: string
    title: string
    description: string
    formula: string
    inputs: WidgetInput[]
    outputs: WidgetOutput[]
    source_citation?: string
}

export interface GithubDiff {
    old_text: string
    new_text: string
    title: string
    highlight_type: "side_by_side" | "unified"
}

export interface Message {
    id: string
    session_id: string
    role: "user" | "assistant"
    content: string
    created_at: string
    token_count?: number
    model_used?: string
    sources?: Source[]
    attachments?: Attachment[]
    feedback_type?: "like" | "dislike"
    saved?: boolean
    failed?: boolean
    originalQuery?: string
    isEditing?: boolean
    isRegenerating?: boolean
    // AK-RAG structured response support
    structured_response?: StructuredResponse
    interactive_widgets?: InteractiveWidget[]
    github_diff?: GithubDiff
    persona?: "wanjiku" | "wakili" | "mwanahabari"
}

export interface Source {
    title: string
    url: string
    source_name: string
    category: string
    excerpt: string
}

export interface Attachment {
    id: string
    filename: string
    file_type: string
    file_size: number
    uploaded_at: string
    processed: boolean
    cloudinary_url?: string
}

export interface ChatSession {
    id: string
    title: string
    message_count: number
    created_at: string
    updated_at: string
}

export interface StreamMetadata {
    token_count?: number
    model_used?: string
    sources?: Source[]
}

export type SharePlatform = "twitter" | "linkedin" | "facebook" | "whatsapp" | "telegram" | "email"

export interface ShareFormatResponse {
    platform: SharePlatform
    content: string | string[]
    character_count?: number
    hashtags?: string[]
    metadata?: Record<string, unknown>
}

export interface ShareSheetState {
    messageId: string
    platform: SharePlatform
    preview?: ShareFormatResponse | null
    isLoading: boolean
    shareLink?: string | null
    shareLinkLoading?: boolean
    posting?: boolean
    generatingImage?: boolean
    shareError?: string | null
    success?: string | null
}

export interface SharePlatformConfig {
    id: SharePlatform
    label: string
    accent: string
    description: string
    icon: ReactNode
}
