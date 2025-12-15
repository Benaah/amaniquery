"use client"

/**
 * Model Settings - Admin Page
 * 
 * WeKnora-style AI model configuration for admins
 */

import { useState, useEffect, ReactNode } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Brain,
  Sparkles,
  Zap,
  Rocket,
  Plus,
  Settings,
  CheckCircle,
  XCircle,
  Key,
  RefreshCw,
  Loader2
} from "lucide-react"

interface ModelConfig {
  apiKey?: string
  maxTokens?: number
  topP?: number
  isDefault?: boolean
  id: string
  name: string
  provider: string
  enabled: boolean
  is_default?: boolean
  status: string
  temperature: number
  max_tokens?: number
  top_p?: number
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function ModelSettingsPage() {
  const [models, setModels] = useState<ModelConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState<ModelConfig | null>(null)

  useEffect(() => {
    fetchModels()
  }, [])

  const fetchModels = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/api/v1/admin/models`)
      if (!response.ok) throw new Error("Failed to fetch models")
      const data = await response.json()
      setModels(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load models")
      // Fallback to default models
      setModels([
        {
            id: "moonshot-v1-8k", name: "Moonshot V1", provider: "Moonshot", enabled: true, is_default: true, status: "connected", temperature: 0.7, max_tokens: 4096,
            apiKey: undefined,
            maxTokens: undefined,
            topP: undefined,
            isDefault: undefined
        },
        {
            id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", provider: "Google", enabled: true, is_default: false, status: "connected", temperature: 0.7, max_tokens: 4096,
            apiKey: undefined,
            maxTokens: undefined,
            topP: undefined,
            isDefault: undefined
        },
        {
            id: "gemini-1.5-pro", name: "Gemini 1.5 Pro", provider: "Google", enabled: true, is_default: false, status: "connected", temperature: 0.7, max_tokens: 8192,
            apiKey: undefined,
            maxTokens: undefined,
            topP: undefined,
            isDefault: undefined
        },
        {
            id: "gpt-4o-mini", name: "GPT-4o Mini", provider: "OpenAI", enabled: false, is_default: false, status: "unconfigured", temperature: 0.7, max_tokens: 4096,
            apiKey: undefined,
            maxTokens: undefined,
            topP: undefined,
            isDefault: undefined
        },
        {
            id: "claude-3.5-sonnet", name: "Claude 3.5 Sonnet", provider: "Anthropic", enabled: false, is_default: false, status: "unconfigured", temperature: 0.7, max_tokens: 4096,
            apiKey: undefined,
            maxTokens: undefined,
            topP: undefined,
            isDefault: undefined
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'Google': return <Sparkles className="h-4 w-4" />
      case 'Moonshot': return <Zap className="h-4 w-4" />
      case 'OpenAI': return <Brain className="h-4 w-4" />
      case 'Anthropic': return <Rocket className="h-4 w-4" />
      default: return <Brain className="h-4 w-4" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'connected':
        return <Badge variant="default" className="bg-green-500"><CheckCircle className="h-3 w-3 mr-1" />Connected</Badge>
      case 'error':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Error</Badge>
      case 'unconfigured':
        return <Badge variant="secondary"><Key className="h-3 w-3 mr-1" />Unconfigured</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const updateModel = (id: string, updates: Partial<ModelConfig>) => {
    setModels(prev => prev.map(m => m.id === id ? { ...m, ...updates } : m))
  }

  const setAsDefault = (id: string) => {
    setModels(prev => prev.map(m => ({ ...m, isDefault: m.id === id })))
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Model Settings</h1>
          <p className="text-muted-foreground">Configure AI models and their parameters</p>
        </div>
        <Button variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Test All Connections
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Configured Models</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{models.filter(m => m.status === 'connected').length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Enabled Models</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{models.filter(m => m.enabled).length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Default Model</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold">{models.find(m => m.isDefault)?.name || 'None'}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Providers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{new Set(models.map(m => m.provider)).size}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>AI Models</CardTitle>
          <CardDescription>Configure model access and parameters</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Model</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Enabled</TableHead>
                <TableHead>Default</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {models.map((model) => (
                <TableRow key={model.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getProviderIcon(model.provider)}
                      <div>
                        <div className="font-medium">{model.name}</div>
                        <div className="text-xs text-muted-foreground font-mono">{model.id}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{model.provider}</Badge>
                  </TableCell>
                  <TableCell>{getStatusBadge(model.status)}</TableCell>
                  <TableCell>
                    <Switch
                      checked={model.enabled}
                      onCheckedChange={(checked: any) => updateModel(model.id, { enabled: checked })}
                      disabled={model.status !== 'connected'}
                    />
                  </TableCell>
                  <TableCell>
                    <Switch
                      checked={model.isDefault ?? model.is_default ?? false}
                      onCheckedChange={() => setAsDefault(model.id)}
                      disabled={!model.enabled}
                    />
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => setSelectedModel(model)}
                          >
                            <Settings className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-lg">
                          <DialogHeader>
                            <DialogTitle>Configure {model.name}</DialogTitle>
                            <DialogDescription>
                              Adjust model parameters and API settings
                            </DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4 py-4">
                            <div className="space-y-2">
                              <Label htmlFor="apiKey">API Key</Label>
                              <Input 
                                id="apiKey" 
                                type="password"
                                placeholder="Enter API key..."
                                defaultValue={model.apiKey}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Temperature: {model.temperature}</Label>
                              <Slider
                                defaultValue={[model.temperature]}
                                max={1}
                                step={0.1}
                                onValueChange={(v) => updateModel(model.id, { temperature: v[0] })}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Max Tokens: {model.maxTokens ?? model.max_tokens ?? 4096}</Label>
                              <Slider
                                defaultValue={[model.maxTokens ?? model.max_tokens ?? 4096]}
                                max={16384}
                                step={256}
                                onValueChange={(v) => updateModel(model.id, { maxTokens: v[0] })}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label>Top P: {model.topP ?? model.top_p ?? 0.7}</Label>
                              <Slider
                                defaultValue={[model.topP ?? model.top_p ?? 0.7]}
                                max={1}
                                step={0.05}
                                onValueChange={(v) => updateModel(model.id, { topP: v[0] })}
                              />
                            </div>
                          </div>
                          <DialogFooter>
                            <Button>Save Changes</Button>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
