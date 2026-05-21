"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Search,
  Zap,
  Filter,
  Sparkles,
  RefreshCw,
  Database,
  TrendingUp,
  Settings,
  CheckCircle,
  Loader2
} from "lucide-react"
import { toast } from "sonner"
import { useAuth } from "@/lib/auth-context"

interface RAGConfig {
  topK: number
  useReranking: boolean
  rerankTopK: number
  useHyDE: boolean
  useMultiQuery: boolean
  queryVariants: number
  useHybridSearch: boolean
  hybridAlpha: number
  enableSemanticCache: boolean
  cacheTTLHours: number
  parallelRetrieval: boolean
  maxNamespaces: number
}

interface BackendRAGConfig {
  top_k: number
  use_reranking: boolean
  rerank_top_k: number
  use_hyde: boolean
  use_multi_query: boolean
  use_hybrid_search: boolean
  hybrid_alpha: number
  parallel_retrieval: boolean
  enable_semantic_cache: boolean
  cache_ttl_hours: number
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const DEFAULT_CONFIG: RAGConfig = {
  topK: 5,
  useReranking: true,
  rerankTopK: 5,
  useHyDE: false,
  useMultiQuery: false,
  queryVariants: 3,
  useHybridSearch: false,
  hybridAlpha: 0.7,
  enableSemanticCache: true,
  cacheTTLHours: 24,
  parallelRetrieval: true,
  maxNamespaces: 5
}

function toBackend(frontend: RAGConfig): BackendRAGConfig {
  return {
    top_k: frontend.topK,
    use_reranking: frontend.useReranking,
    rerank_top_k: frontend.rerankTopK,
    use_hyde: frontend.useHyDE,
    use_multi_query: frontend.useMultiQuery,
    use_hybrid_search: frontend.useHybridSearch,
    hybrid_alpha: frontend.hybridAlpha,
    parallel_retrieval: frontend.parallelRetrieval,
    enable_semantic_cache: frontend.enableSemanticCache,
    cache_ttl_hours: frontend.cacheTTLHours,
  }
}

function fromBackend(backend: BackendRAGConfig): RAGConfig {
  return {
    ...DEFAULT_CONFIG,
    topK: backend.top_k,
    useReranking: backend.use_reranking,
    rerankTopK: backend.rerank_top_k,
    useHyDE: backend.use_hyde,
    useMultiQuery: backend.use_multi_query,
    useHybridSearch: backend.use_hybrid_search,
    hybridAlpha: backend.hybrid_alpha,
    parallelRetrieval: backend.parallel_retrieval,
    enableSemanticCache: backend.enable_semantic_cache,
    cacheTTLHours: backend.cache_ttl_hours,
  }
}

export default function RAGSettingsPage() {
  const [config, setConfig] = useState<RAGConfig>(DEFAULT_CONFIG)
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const { user } = useAuth()

  useEffect(() => {
    const loadConfig = async () => {
      setIsLoading(true)
      try {
        const sessionToken = localStorage.getItem("session_token")
        const response = await fetch(`${API_URL}/api/v1/admin/rag/config`, {
          headers: {
            "Content-Type": "application/json",
            "X-Session-Token": sessionToken || "",
          },
        })
        if (!response.ok) {
          throw new Error("Failed to load configuration")
        }
        const data: BackendRAGConfig = await response.json()
        setConfig(fromBackend(data))
      } catch (error) {
        console.error("Failed to load RAG config:", error)
        toast.error("Failed to load configuration")
      } finally {
        setIsLoading(false)
      }
    }
    loadConfig()
  }, [])

  const updateConfig = <K extends keyof RAGConfig>(key: K, value: RAGConfig[K]) => {
    setConfig(prev => ({ ...prev, [key]: value }))
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const sessionToken = localStorage.getItem("session_token")
      const body = toBackend(config)
      const response = await fetch(`${API_URL}/api/v1/admin/rag/config`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": sessionToken || "",
        },
        body: JSON.stringify(body),
      })
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || "Failed to save configuration")
      }
      const data: BackendRAGConfig = await response.json()
      setConfig(fromBackend(data))
      toast.success("Configuration saved successfully")
    } catch (error) {
      console.error("Failed to save RAG config:", error)
      toast.error(error instanceof Error ? error.message : "Failed to save configuration")
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">RAG Pipeline Settings</h1>
          <p className="text-muted-foreground">Configure retrieval and generation parameters</p>
        </div>
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle className="h-4 w-4 mr-2" />}
          Save Changes
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Top K</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{config.topK}</div>
            <p className="text-xs text-muted-foreground">Documents retrieved</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Re-ranking</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{config.useReranking ? "Enabled" : "Disabled"}</div>
            <p className="text-xs text-muted-foreground">Intelligent filtering</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Hybrid α</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{config.hybridAlpha.toFixed(1)}</div>
            <p className="text-xs text-muted-foreground">Vector vs BM25 balance</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Cache TTL</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{config.cacheTTLHours}h</div>
            <p className="text-xs text-muted-foreground">Result caching</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="retrieval" className="space-y-4">
        <TabsList>
          <TabsTrigger value="retrieval">
            <Search className="h-4 w-4 mr-2" />
            Retrieval
          </TabsTrigger>
          <TabsTrigger value="expansion">
            <Sparkles className="h-4 w-4 mr-2" />
            Query Expansion
          </TabsTrigger>
          <TabsTrigger value="hybrid">
            <Database className="h-4 w-4 mr-2" />
            Hybrid Search
          </TabsTrigger>
          <TabsTrigger value="performance">
            <Zap className="h-4 w-4 mr-2" />
            Performance
          </TabsTrigger>
        </TabsList>

        <TabsContent value="retrieval">
          <Card>
            <CardHeader>
              <CardTitle>Retrieval Settings</CardTitle>
              <CardDescription>Configure document retrieval parameters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Top K: {config.topK}</Label>
                <Slider
                  value={[config.topK]}
                  min={1}
                  max={20}
                  step={1}
                  onValueChange={(v) => updateConfig('topK', v[0])}
                />
                <p className="text-xs text-muted-foreground">Number of documents to retrieve</p>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Intelligent Re-ranking</Label>
                  <p className="text-xs text-muted-foreground">Use cross-encoder to filter relevant docs</p>
                </div>
                <Switch
                  checked={config.useReranking}
                  onCheckedChange={(v: boolean) => updateConfig('useReranking', v)}
                />
              </div>

              {config.useReranking && (
                <div className="space-y-2 ml-4 p-4 bg-muted/50 rounded-lg">
                  <Label>Re-rank Top K: {config.rerankTopK}</Label>
                  <Slider
                    value={[config.rerankTopK]}
                    min={1}
                    max={10}
                    step={1}
                    onValueChange={(v) => updateConfig('rerankTopK', v[0])}
                  />
                  <p className="text-xs text-muted-foreground">Documents after re-ranking</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="expansion">
          <Card>
            <CardHeader>
              <CardTitle>Query Expansion</CardTitle>
              <CardDescription>Improve recall with query expansion techniques</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>HyDE (Hypothetical Document Embeddings)</Label>
                  <p className="text-xs text-muted-foreground">Generate hypothetical answer, then search</p>
                </div>
                <Switch
                  checked={config.useHyDE}
                  onCheckedChange={(v: boolean) => updateConfig('useHyDE', v)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Multi-Query</Label>
                  <p className="text-xs text-muted-foreground">Generate multiple query variants</p>
                </div>
                <Switch
                  checked={config.useMultiQuery}
                  onCheckedChange={(v: boolean) => updateConfig('useMultiQuery', v)}
                />
              </div>

              {config.useMultiQuery && (
                <div className="space-y-2 ml-4 p-4 bg-muted/50 rounded-lg">
                  <Label>Query Variants: {config.queryVariants}</Label>
                  <Slider
                    value={[config.queryVariants]}
                    min={2}
                    max={5}
                    step={1}
                    onValueChange={(v) => updateConfig('queryVariants', v[0])}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="hybrid">
          <Card>
            <CardHeader>
              <CardTitle>Hybrid Search</CardTitle>
              <CardDescription>Combine vector and keyword search</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Hybrid Search</Label>
                  <p className="text-xs text-muted-foreground">Combine BM25 + vector similarity</p>
                </div>
                <Switch
                  checked={config.useHybridSearch}
                  onCheckedChange={(v: boolean) => updateConfig('useHybridSearch', v)}
                />
              </div>

              {config.useHybridSearch && (
                <div className="space-y-2">
                  <Label>Hybrid Alpha: {config.hybridAlpha.toFixed(2)}</Label>
                  <Slider
                    value={[config.hybridAlpha]}
                    min={0}
                    max={1}
                    step={0.05}
                    onValueChange={(v) => updateConfig('hybridAlpha', v[0])}
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>BM25 (keywords)</span>
                    <span>Vector (semantic)</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance">
          <Card>
            <CardHeader>
              <CardTitle>Performance Settings</CardTitle>
              <CardDescription>Optimize speed and caching</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Parallel Retrieval</Label>
                  <p className="text-xs text-muted-foreground">Query all namespaces simultaneously</p>
                </div>
                <Switch
                  checked={config.parallelRetrieval}
                  onCheckedChange={(v: boolean) => updateConfig('parallelRetrieval', v)}
                />
              </div>

              <div className="space-y-2">
                <Label>Max Namespaces: {config.maxNamespaces}</Label>
                <Slider
                  value={[config.maxNamespaces]}
                  min={1}
                  max={10}
                  step={1}
                  onValueChange={(v) => updateConfig('maxNamespaces', v[0])}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Semantic Cache</Label>
                  <p className="text-xs text-muted-foreground">Cache similar query results</p>
                </div>
                <Switch
                  checked={config.enableSemanticCache}
                  onCheckedChange={(v: boolean) => updateConfig('enableSemanticCache', v)}
                />
              </div>

              {config.enableSemanticCache && (
                <div className="space-y-2 ml-4 p-4 bg-muted/50 rounded-lg">
                  <Label>Cache TTL: {config.cacheTTLHours} hours</Label>
                  <Slider
                    value={[config.cacheTTLHours]}
                    min={1}
                    max={168}
                    step={1}
                    onValueChange={(v) => updateConfig('cacheTTLHours', v[0])}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
