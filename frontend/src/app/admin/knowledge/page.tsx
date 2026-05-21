"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/lib/auth-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
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
  Database,
  Plus,
  Upload,
  RefreshCw,
  Trash2,
  FileText,
  Scale,
  Newspaper,
  CheckCircle,
  XCircle,
  Clock,
  Settings,
  Loader2,
} from "lucide-react"
import { toast } from "sonner"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface KnowledgeBase {
  id: string
  name: string
  description: string
  type: "legal" | "news" | "general" | "custom"
  document_count: number
  status: "active" | "indexing" | "error"
  last_updated: string | null
}

export default function KnowledgeBaseSettingsPage() {
  const { isAuthenticated, isAdmin } = useAuth()

  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    type: "legal",
    description: "",
    chunkSize: 512,
    embeddingModel: "text-embedding-3-small",
  })

  useEffect(() => {
    if (isAuthenticated && isAdmin) {
      fetchKnowledgeBases()
    }
  }, [isAuthenticated, isAdmin])

  const fetchKnowledgeBases = async () => {
    setLoading(true)
    setError(null)
    try {
      const sessionToken = localStorage.getItem("session_token")
      const response = await fetch(`${API_URL}/api/v1/admin/knowledge-bases`, {
        headers: {
          "X-Session-Token": sessionToken || "",
        },
      })

      if (response.ok) {
        const data = await response.json()
        setKnowledgeBases(data)
      } else {
        const errMsg = "Failed to fetch knowledge bases"
        setError(errMsg)
        toast.error(errMsg)
      }
    } catch {
      const errMsg = "Failed to fetch knowledge bases"
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!formData.name.trim()) {
      toast.error("Name is required")
      return
    }
    setIsCreating(false)
    try {
      const sessionToken = localStorage.getItem("session_token")
      const response = await fetch(`${API_URL}/api/v1/admin/knowledge-bases`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": sessionToken || "",
        },
        body: JSON.stringify({
          name: formData.name,
          type: formData.type,
          description: formData.description,
          chunk_size: formData.chunkSize,
          embedding_model: formData.embeddingModel,
        }),
      })
      if (response.ok) {
        toast.success("Knowledge base created")
        setFormData({
          name: "",
          type: "legal",
          description: "",
          chunkSize: 512,
          embeddingModel: "text-embedding-3-small",
        })
        await fetchKnowledgeBases()
      } else {
        const err = await response.text()
        toast.error(err || "Failed to create knowledge base")
      }
    } catch {
      toast.error("Failed to create knowledge base")
    }
  }

  const handleDelete = async (id: string) => {
    try {
      const sessionToken = localStorage.getItem("session_token")
      const response = await fetch(`${API_URL}/api/v1/admin/knowledge-bases/${id}`, {
        method: "DELETE",
        headers: {
          "X-Session-Token": sessionToken || "",
        },
      })
      if (response.ok || response.status === 204) {
        toast.success("Knowledge base deleted")
        await fetchKnowledgeBases()
      } else {
        const err = await response.text()
        toast.error(err || "Failed to delete knowledge base")
      }
    } catch {
      toast.error("Failed to delete knowledge base")
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "legal":
        return <Scale className="h-4 w-4" />
      case "news":
        return <Newspaper className="h-4 w-4" />
      default:
        return <Database className="h-4 w-4" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return (
          <Badge variant="default" className="bg-green-500">
            <CheckCircle className="h-3 w-3 mr-1" />
            Active
          </Badge>
        )
      case "indexing":
        return (
          <Badge variant="secondary">
            <Clock className="h-3 w-3 mr-1 animate-spin" />
            Indexing
          </Badge>
        )
      case "error":
        return (
          <Badge variant="destructive">
            <XCircle className="h-3 w-3 mr-1" />
            Error
          </Badge>
        )
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Base Management</h1>
          <p className="text-muted-foreground">Manage your document collections and search indices</p>
        </div>
        <Dialog open={isCreating} onOpenChange={setIsCreating}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Knowledge Base
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create Knowledge Base</DialogTitle>
              <DialogDescription>
                Create a new knowledge base for document retrieval
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., Kenya Law"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="type">Type</Label>
                  <select
                    className="w-full p-2 border rounded-md"
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  >
                    <option value="legal">Legal</option>
                    <option value="news">News</option>
                    <option value="general">General</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe this knowledge base..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="chunkSize">Chunk Size</Label>
                  <Input
                    id="chunkSize"
                    type="number"
                    value={formData.chunkSize}
                    onChange={(e) => setFormData({ ...formData, chunkSize: Number(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="embeddingModel">Embedding Model</Label>
                  <select
                    className="w-full p-2 border rounded-md"
                    value={formData.embeddingModel}
                    onChange={(e) => setFormData({ ...formData, embeddingModel: e.target.value })}
                  >
                    <option value="text-embedding-3-small">text-embedding-3-small</option>
                    <option value="text-embedding-3-large">text-embedding-3-large</option>
                    <option value="text-embedding-ada-002">text-embedding-ada-002</option>
                  </select>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreating(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreate}>Create</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Knowledge Bases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{knowledgeBases.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {knowledgeBases.reduce((sum, kb) => sum + kb.document_count, 0).toLocaleString()}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Indices</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {knowledgeBases.filter((kb) => kb.status === "active").length}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Knowledge Bases</CardTitle>
          <CardDescription>Manage document collections and search indices</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : error ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>Failed to load knowledge bases.</p>
              <Button variant="outline" className="mt-4" onClick={fetchKnowledgeBases}>
                Retry
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Documents</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {knowledgeBases.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      No knowledge bases found. Create one to get started.
                    </TableCell>
                  </TableRow>
                ) : (
                  knowledgeBases.map((kb) => (
                    <TableRow key={kb.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getTypeIcon(kb.type)}
                          <div>
                            <div className="font-medium">{kb.name}</div>
                            <div className="text-xs text-muted-foreground">{kb.description}</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{kb.type}</Badge>
                      </TableCell>
                      <TableCell>{kb.document_count.toLocaleString()}</TableCell>
                      <TableCell>{getStatusBadge(kb.status)}</TableCell>
                      <TableCell>
                        {kb.last_updated
                          ? new Date(kb.last_updated).toLocaleDateString()
                          : "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => toast.info("Document upload coming in next release")}
                          >
                            <Upload className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={async () => {
                              toast.info("Refreshing knowledge base...")
                              await fetchKnowledgeBases()
                              toast.success("Knowledge base refreshed")
                            }}
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => toast.info("Settings coming in next release")}
                          >
                            <Settings className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => handleDelete(kb.id)}>
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
