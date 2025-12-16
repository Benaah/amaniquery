import { get, put } from '@/utils/request'

export interface SystemInfo {
  version: string
  commit_id?: string
  build_time?: string
  go_version?: string
  keyword_index_engine?: string
  vector_store_engine?: string
  graph_database_engine?: string
  minio_enabled?: boolean
}

export interface ToolDefinition {
  name: string
  label: string
  description: string
}

export interface PlaceholderDefinition {
  name: string
  label: string
  description: string
}

export interface AgentConfig {
  max_iterations: number
  reflection_enabled: boolean
  allowed_tools: string[]
  temperature: number
  knowledge_bases?: string[]
  system_prompt_web_enabled?: string  // Custom system prompt when web search is enabled
  system_prompt_web_disabled?: string // Custom system prompt when web search is disabled
  use_custom_system_prompt?: boolean
  available_tools?: ToolDefinition[]  // GET 响应中包含，POST/PUT 不需要
  available_placeholders?: PlaceholderDefinition[]  // GET 响应中包含，POST/PUT 不需要
}

export interface ConversationConfig {
  prompt: string
  context_template: string
  temperature: number
  max_completion_tokens: number
  use_custom_system_prompt?: boolean
  use_custom_context_template?: boolean
  max_rounds: number
  embedding_top_k: number
  keyword_threshold: number
  vector_threshold: number
  rerank_top_k: number
  rerank_threshold: number
  enable_rewrite: boolean
  fallback_strategy: string
  fallback_response: string
  fallback_prompt?: string
  summary_model_id?: string
  rerank_model_id?: string
  rewrite_prompt_system?: string
  rewrite_prompt_user?: string
  enable_query_expansion?: boolean
}

export function getSystemInfo(): Promise<{ data: SystemInfo }> {
  return get('/api/v1/system/info')
}

export function getAgentConfig(): Promise<{ data: AgentConfig }> {
  return get('/api/v1/tenants/kv/agent-config')
}

export function updateAgentConfig(config: AgentConfig): Promise<{ data: AgentConfig }> {
  return put('/api/v1/tenants/kv/agent-config', config)
}

export function getConversationConfig(): Promise<{ data: ConversationConfig }> {
  return get('/api/v1/tenants/kv/conversation-config')
}

export function updateConversationConfig(config: ConversationConfig): Promise<{ data: ConversationConfig }> {
  return put('/api/v1/tenants/kv/conversation-config', config)
}
