export interface Attachment {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  uploaded_at: string;
  processed: boolean;
  cloudinary_url?: string;
  transcript?: string;
  frame_urls?: string[];
  duration_seconds?: number;
}

export interface Source {
  title: string;
  url: string;
  source_name: string;
  category: string;
  excerpt: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  token_count?: number;
  model_used?: string;
  sources?: Source[];
  attachments?: Attachment[];
  feedback_type?: 'like' | 'dislike';
  saved?: boolean;
  failed?: boolean;
  stopped?: boolean;
  originalQuery?: string;
  persona?: 'wanjiku' | 'wakili' | 'mwanahabari';
  isResearch?: boolean;
  researchBundle?: ResearchBundle;
}

export interface ChatSession {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface StreamMetadata {
  token_count?: number;
  model_used?: string;
  sources?: Source[];
  researchBundle?: ResearchBundle;
}

export interface ResearchBundle {
  bundle_id: string;
  has_pdf: boolean;
  has_docx: boolean;
  download_urls: {
    pdf?: string;
    docx?: string;
  };
}

export interface NotificationSubscription {
  id: string;
  phone_number: string;
  delivery_method: string;
  categories: string[];
  sources: string[];
  active: boolean;
  created_at: string;
}

export interface NotificationSource {
  id: string;
  name: string;
  type: string;
}

export interface VoiceTokenResponse {
  token: string;
  expires_at: string;
  region: string;
}

export interface APIError {
  message: string;
  status?: number;
  details?: string;
}

export interface ResearchResult {
  bundle_id: string;
  query: string;
  created_at: string;
  status: string;
  analysis_summary?: string;
  sources?: Source[];
  analysis?: any;
  has_pdf: boolean;
  has_docx: boolean;
  download_urls: {
    pdf?: string;
    docx?: string;
  };
  error?: string;
}

export interface StreamEvent {
  type: 'tool_start' | 'tool_result' | 'sources' | 'content' | 'done' | 'error';
  tool_name?: string;
  query?: string;
  status?: string;
  latency_ms?: number;
  content?: string;
  sources?: Source[];
  full_answer?: string;
  is_research?: boolean;
  bundle?: ResearchBundle;
  error?: string;
}
