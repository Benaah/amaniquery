import { get, put } from '@/utils/request'

// WebSearchProviderConfig represents information about a web search provider
export interface WebSearchProviderConfig {
  id: string
  name: string
  free: boolean
  requires_api_key: boolean
  description?: string
  api_url?: string
}

// WebSearchConfig represents the web search configuration for a tenant
export interface WebSearchConfig {
  provider: string
  api_key?: string
  max_results: number
  include_date: boolean
  compression_method: string
  blacklist: string[]
  embedding_model_id?: string
  embedding_dimension?: number
  rerank_model_id?: string
  document_fragments?: number
}

// Get web search providers
export function getWebSearchProviders() {
  return get('/api/v1/web-search/providers')
}

// Get tenant web search config via KV API
export function getTenantWebSearchConfig() {
  return get('/api/v1/tenants/kv/web-search-config')
}

// Update tenant web search config via KV API
export function updateTenantWebSearchConfig(config: WebSearchConfig) {
  return put('/api/v1/tenants/kv/web-search-config', config)
}

