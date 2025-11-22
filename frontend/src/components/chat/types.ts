import type { ReactNode } from "react"

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

export type SharePlatform = "twitter" | "linkedin" | "facebook"

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
