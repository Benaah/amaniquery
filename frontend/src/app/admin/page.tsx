"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { 
  Database, 
  Activity, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Play, 
  Search,
  BarChart3,
  FileText,
  Globe
} from "lucide-react"
import Link from "next/link"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Stats {
  total_chunks: number
  categories: Record<string, number>
  sources: string[]
}

interface Health {
  status: string
  database_chunks: number
  embedding_model: string
  llm_provider: string
}

interface Crawler {
  status: "idle" | "running" | "failed"
  last_run: string
  logs: string[]
}
interface CommandResult { 
  command: string
  exit_code: number
  stdout: string
  stderr: string
}

interface Document {
  id: string
  content: string
  metadata: {
    title: string
    url: string
    source: string
    category: string
    date: string
    author?: string
    sentiment_polarity?: number
    sentiment_label?: string
  }
  score: number
}

interface ConfigEntry {
  description: string
  has_value: boolean
}

interface ConfigData {
  [key: string]: ConfigEntry
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [health, setHealth] = useState<Health | null>(null)
  const [crawlers, setCrawlers] = useState<Record<string, Crawler>>({})
  const [documents, setDocuments] = useState<Document[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCrawler, setSelectedCrawler] = useState<string | null>(null)
  const [command, setCommand] = useState("")
  const [commandHistory, setCommandHistory] = useState<CommandResult[]>([])
  const [isExecuting, setIsExecuting] = useState(false)
  const [configs, setConfigs] = useState<ConfigData>({})
  const [newConfigKey, setNewConfigKey] = useState("")
  const [newConfigValue, setNewConfigValue] = useState("")
  const [newConfigDescription, setNewConfigDescription] = useState("")

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/stats`)
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error)
    }
  }

  const fetchHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`)
      if (response.ok) {
        const data = await response.json()
        setHealth(data)
      }
    } catch (error) {
      console.error("Failed to fetch health:", error)
    }
  }

  const fetchCrawlers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/crawlers`)
      if (response.ok) {
        const data = await response.json()
        setCrawlers(data.crawlers || {})
      } else {
        console.error("Failed to fetch crawlers:", response.status)
        setCrawlers({})
      }
    } catch (error) {
      console.error("Failed to fetch crawlers:", error)
      setCrawlers({})
    }
  }

  const fetchConfigs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/config`)
      if (response.ok) {
        const data = await response.json()
        setConfigs(data)
      }
    } catch (error) {
      console.error("Failed to fetch configs:", error)
    }
  }

  const searchDocuments = async () => {
    try {
      const params = new URLSearchParams()
      if (searchQuery) params.append("query", searchQuery)
      params.append("limit", "100")

      const response = await fetch(`${API_BASE_URL}/admin/documents?${params}`)
      if (response.ok) {
        const data = await response.json()
        setDocuments(data.documents)
      }
    } catch (error) {
      console.error("Failed to search documents:", error)
    }
  }

  const executeCommand = async () => {
    if (!command.trim()) return

    setIsExecuting(true)
    try {
      const response = await fetch(`${API_BASE_URL}/admin/execute`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ command }),
      })

      if (response.ok) {
        const result: CommandResult = await response.json()
        setCommandHistory(prev => [result, ...prev.slice(0, 9)]) // Keep last 10
        setCommand("")
      }
    } catch (error) {
      console.error("Failed to execute command:", error)
    } finally {
      setIsExecuting(false)
    }
  }

  useEffect(() => {
    fetchStats()
    fetchHealth()
    fetchCrawlers()
    fetchConfigs()
  }, [])

  const runCrawler = async (crawlerName: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/crawlers/${crawlerName}/start`, {
        method: "POST",
      })
      if (response.ok) {
        // Refresh crawler status
        fetchCrawlers()
      }
    } catch (error) {
      console.error("Failed to start crawler:", error)
    }
  }

  const setConfig = async () => {
    if (!newConfigKey.trim() || !newConfigValue.trim()) return

    try {
      const response = await fetch(`${API_BASE_URL}/admin/config`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          key: newConfigKey,
          value: newConfigValue,
          description: newConfigDescription
        }),
      })
      if (response.ok) {
        setNewConfigKey("")
        setNewConfigValue("")
        setNewConfigDescription("")
        fetchConfigs()
      }
    } catch (error) {
      console.error("Failed to set config:", error)
    }
  }

  const deleteConfig = async (key: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/config/${key}`, {
        method: "DELETE",
      })
      if (response.ok) {
        fetchConfigs()
      }
    } catch (error) {
      console.error("Failed to delete config:", error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy": return "text-green-600"
      case "running": return "text-blue-600"
      case "failed": return "text-red-600"
      default: return "text-gray-600"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy": return <CheckCircle className="w-4 h-4" />
      case "running": return <Activity className="w-4 h-4" />
      case "failed": return <XCircle className="w-4 h-4" />
      default: return <Clock className="w-4 h-4" />
    }
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-6">
      <div className="max-w-7xl mx-auto space-y-4 md:space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">Admin Dashboard</h1>
            <p className="text-sm md:text-base text-muted-foreground">Control Panel for AmaniQuery System</p>
          </div>
          <Link href="/">
            <Button variant="outline" className="w-full sm:w-auto min-h-[44px]">
              <Globe className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            </CardHeader>
            <CardContent>
              <div className="text-xl md:text-2xl font-bold">
                {stats?.total_chunks || health?.database_chunks || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Vector database chunks
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Vector DB Status</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                {getStatusIcon(health?.status || "unknown")}
                <span className={`text-sm font-medium ${getStatusColor(health?.status || "unknown")}`}>
                  {health?.status || "Unknown"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                {health?.embedding_model || "Loading..."}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Status</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            </CardHeader>
            <CardContent>
              <div className="text-lg md:text-2xl font-bold">
                Active
              </div>
              <p className="text-xs text-muted-foreground">
                System operational
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">API Health</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                {health ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <span className={`text-sm font-medium ${getStatusColor("healthy")}`}>Online</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
                    <span className={`text-sm font-medium ${getStatusColor("failed")}`}>Offline</span>
                  </>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                {health?.llm_provider || "Checking..."}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Crawler Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg md:text-xl">
              <BarChart3 className="w-5 h-5 mr-2" />
              Crawler Management
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="min-w-[120px]">Crawler</TableHead>
                    <TableHead className="min-w-[80px]">Status</TableHead>
                    <TableHead className="min-w-[120px]">Last Run</TableHead>
                    <TableHead className="min-w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {crawlers && Object.keys(crawlers).length > 0 ? (
                    Object.entries(crawlers).map(([name, crawler]) => (
                      <TableRow key={name}>
                        <TableCell className="font-medium capitalize text-sm md:text-base">
                          {name.replace('_', ' ')}
                        </TableCell>
                        <TableCell>
                          <Badge variant={
                            crawler.status === "running" ? "default" :
                            crawler.status === "failed" ? "destructive" : "secondary"
                          } className="text-xs">
                            {crawler.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs md:text-sm">
                          {new Date(crawler.last_run).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-1 md:space-x-2">
                            <Button
                              size="sm"
                              onClick={() => runCrawler(name)}
                              disabled={crawler.status === "running"}
                              className="h-8 px-2 md:px-3 text-xs md:text-sm min-w-[60px]"
                            >
                              <Play className="w-3 h-3 mr-1" />
                              Run
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setSelectedCrawler(name)}
                              className="h-8 px-2 md:px-3 text-xs md:text-sm"
                            >
                              Logs
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-muted-foreground py-6 md:py-8 text-sm">
                        No crawlers available or loading...
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Log Viewer */}
        {selectedCrawler && crawlers && crawlers[selectedCrawler] && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg md:text-xl">Logs - {selectedCrawler.replace('_', ' ')}</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea
                value={crawlers[selectedCrawler].logs?.join('\n') || "No logs available"}
                readOnly
                className="min-h-[150px] md:min-h-[200px] font-mono text-xs md:text-sm"
              />
            </CardContent>
          </Card>
        )}

        {/* Command Shell */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg md:text-xl">
              <Activity className="w-5 h-5 mr-2" />
              Command Shell
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 md:space-y-4">
              <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                <Input
                  placeholder="Enter command to execute..."
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && executeCommand()}
                  className="flex-1 font-mono text-sm md:text-base h-10 md:h-11"
                  disabled={isExecuting}
                />
                <Button 
                  onClick={executeCommand} 
                  disabled={isExecuting || !command.trim()}
                  className="w-full sm:w-auto min-h-[44px] px-4 md:px-6"
                >
                  {isExecuting ? "Running..." : "Execute"}
                </Button>
              </div>
              
              <div className="space-y-2 max-h-64 md:max-h-96 overflow-y-auto">
                {commandHistory.map((result, index) => (
                  <Card key={index} className="bg-muted">
                    <CardContent className="p-3 md:p-4">
                      <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-2 mb-2">
                        <span className="font-mono text-xs md:text-sm text-muted-foreground">$</span>
                        <code className="font-mono text-xs md:text-sm flex-1 break-all">{result.command}</code>
                        <Badge variant={result.exit_code === 0 ? "secondary" : "destructive"} className="text-xs w-fit">
                          Exit: {result.exit_code}
                        </Badge>
                      </div>
                      {result.stdout && (
                        <pre className="text-xs font-mono bg-background p-2 rounded border overflow-x-auto whitespace-pre-wrap">
                          {result.stdout}
                        </pre>
                      )}
                      {result.stderr && (
                        <pre className="text-xs font-mono bg-destructive/10 text-destructive p-2 rounded border overflow-x-auto whitespace-pre-wrap">
                          {result.stderr}
                        </pre>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Data Explorer */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg md:text-xl">
              <Search className="w-5 h-5 mr-2" />
              Data Explorer
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 md:space-y-4">
              <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                <Input
                  placeholder="Search documents by keyword, source, or date..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && searchDocuments()}
                  className="flex-1 h-10 md:h-11 text-sm md:text-base"
                />
                <Button 
                  onClick={searchDocuments}
                  className="w-full sm:w-auto min-h-[44px] px-4 md:px-6"
                >
                  <Search className="w-4 h-4 mr-2" />
                  Search
                </Button>
              </div>
              
              {documents.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Found {documents.length} documents
                  </p>
                  <div className="max-h-64 md:max-h-96 overflow-y-auto space-y-2">
                    {documents.slice(0, 20).map((doc) => (
                      <Card key={doc.id} className="cursor-pointer hover:bg-muted/50">
                        <CardContent className="p-3 md:p-4">
                          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-2 gap-2">
                            <h4 className="font-medium text-sm md:text-base line-clamp-1">
                              {doc.metadata.title || "Untitled"}
                            </h4>
                            <Badge variant="outline" className="text-xs w-fit flex-shrink-0">
                              {doc.metadata.category}
                            </Badge>
                          </div>
                          <p className="text-xs md:text-sm text-muted-foreground mb-2 line-clamp-2">
                            {doc.content.substring(0, 200)}...
                          </p>
                          <div className="flex flex-col sm:flex-row sm:justify-between text-xs text-muted-foreground gap-1">
                            <span className="truncate">{doc.metadata.source}</span>
                            <span className="flex-shrink-0">{doc.metadata.date}</span>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="text-xs md:text-sm text-muted-foreground bg-muted/50 p-3 rounded-lg">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <div><strong>Categories:</strong> {stats ? Object.keys(stats.categories).join(", ") : "Loading..."}</div>
                  <div><strong>Sources:</strong> {stats ? stats.sources.join(", ") : "Loading..."}</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Configuration Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg md:text-xl">
              <Database className="w-5 h-5 mr-2" />
              Configuration Management
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Add New Config */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  placeholder="Config Key (e.g., ELASTICSEARCH_URL)"
                  value={newConfigKey}
                  onChange={(e) => setNewConfigKey(e.target.value)}
                  className="text-sm"
                />
                <Input
                  placeholder="Config Value"
                  value={newConfigValue}
                  onChange={(e) => setNewConfigValue(e.target.value)}
                  type="password"
                  className="text-sm"
                />
                <div className="flex space-x-2">
                  <Input
                    placeholder="Description (optional)"
                    value={newConfigDescription}
                    onChange={(e) => setNewConfigDescription(e.target.value)}
                    className="flex-1 text-sm"
                  />
                  <Button 
                    onClick={setConfig}
                    disabled={!newConfigKey.trim() || !newConfigValue.trim()}
                    className="px-4"
                  >
                    Add
                  </Button>
                </div>
              </div>

              {/* Config List */}
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Current Configurations</h4>
                <div className="max-h-64 overflow-y-auto space-y-2">
                  {Object.entries(configs).map(([key, config]) => (
                    <Card key={key} className="bg-muted/50">
                      <CardContent className="p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="font-mono text-sm font-medium truncate">{key}</div>
                            <div className="text-xs text-muted-foreground">{config.description || "No description"}</div>
                          </div>
                          <div className="flex items-center space-x-2 ml-4">
                            <Badge variant={config.has_value ? "secondary" : "outline"} className="text-xs">
                              {config.has_value ? "Set" : "Empty"}
                            </Badge>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => deleteConfig(key)}
                              className="h-8 px-2 text-xs"
                            >
                              Delete
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  {Object.keys(configs).length === 0 && (
                    <div className="text-center text-muted-foreground py-4 text-sm">
                      No configurations found
                    </div>
                  )}
                </div>
              </div>

              {/* Common Config Templates */}
              <div className="text-xs text-muted-foreground bg-muted/50 p-3 rounded-lg">
                <div className="font-medium mb-2">Common Configuration Keys:</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-1 text-xs">
                  <div>• ELASTICSEARCH_URL - Elasticsearch cloud URL</div>
                  <div>• ELASTICSEARCH_API_KEY - Elasticsearch API key</div>
                  <div>• UPSTASH_VECTOR_URL - Upstash Vector URL</div>
                  <div>• UPSTASH_VECTOR_TOKEN - Upstash Vector token</div>
                  <div>• QDRANT_URL - QDrant cloud URL</div>
                  <div>• QDRANT_API_KEY - QDrant API key</div>
                  <div>• UPSTASH_REDIS_URL - Upstash Redis URL</div>
                  <div>• UPSTASH_REDIS_TOKEN - Upstash Redis token</div>
                  <div>• LLM_PROVIDER - LLM provider (moonshot, openai, etc.)</div>
                  <div>• GEMINI_API_KEY - Gemini API key</div>
                  <div>• OPENAI_API_KEY - OpenAI API key</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}