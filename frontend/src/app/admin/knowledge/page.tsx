"use client"

/**
 * Knowledge Base Settings - Admin Page
 * 
 * WeKnora-style knowledge base management for admins
 */

import { useState } from "react"
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
  Edit,
  FileText,
  Scale,
  Newspaper,
  CheckCircle,
  XCircle,
  Clock,
  Settings,
  Search
} from "lucide-react"


interface KnowledgeBase {
  id: string
  name: string
  description: string
  type: 'legal' | 'news' | 'general' | 'custom'
  documentCount: number
  lastUpdated: string
  status: 'active' | 'indexing' | 'error'
  chunkSize: number
  embeddingModel: string
}

const MOCK_KNOWLEDGE_BASES: KnowledgeBase[] = [
  {
    id: "kenya_law",
    name: "Kenya Law",
    description: "Constitution, Acts, Bills, Case Law from Kenya Law Reports",
    type: "legal",
    documentCount: 5420,
    lastUpdated: "2025-12-14T10:30:00Z",
    status: "active",
    chunkSize: 512,
    embeddingModel: "text-embedding-3-small"
  },
  {
    id: "kenya_news",
    name: "Kenya News",
    description: "Current affairs from major Kenyan news outlets",
    type: "news",
    documentCount: 12350,
    lastUpdated: "2025-12-15T08:00:00Z",
    status: "active",
    chunkSize: 256,
    embeddingModel: "text-embedding-3-small"
  },
  {
    id: "parliament",
    name: "Parliament Records",
    description: "Bills, Hansard, Committee Reports",
    type: "legal",
    documentCount: 2100,
    lastUpdated: "2025-12-13T14:20:00Z",
    status: "indexing",
    chunkSize: 512,
    embeddingModel: "text-embedding-3-small"
  }
]

export default function KnowledgeBaseSettingsPage() {
  const [knowledgeBases, setKnowledgeBases] = useState(MOCK_KNOWLEDGE_BASES)
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null)
  const [isCreating, setIsCreating] = useState(false)

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'legal': return <Scale className="h-4 w-4" />
      case 'news': return <Newspaper className="h-4 w-4" />
      default: return <Database className="h-4 w-4" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="default" className="bg-green-500"><CheckCircle className="h-3 w-3 mr-1" />Active</Badge>
      case 'indexing':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1 animate-spin" />Indexing</Badge>
      case 'error':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Error</Badge>
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
                  <Input id="name" placeholder="e.g., Kenya Law" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="type">Type</Label>
                  <select className="w-full p-2 border rounded-md">
                    <option value="legal">Legal</option>
                    <option value="news">News</option>
                    <option value="general">General</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea id="description" placeholder="Describe this knowledge base..." />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="chunkSize">Chunk Size</Label>
                  <Input id="chunkSize" type="number" defaultValue={512} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="embeddingModel">Embedding Model</Label>
                  <select className="w-full p-2 border rounded-md">
                    <option value="text-embedding-3-small">text-embedding-3-small</option>
                    <option value="text-embedding-3-large">text-embedding-3-large</option>
                    <option value="text-embedding-ada-002">text-embedding-ada-002</option>
                  </select>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreating(false)}>Cancel</Button>
              <Button onClick={() => setIsCreating(false)}>Create</Button>
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
              {knowledgeBases.reduce((sum, kb) => sum + kb.documentCount, 0).toLocaleString()}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Indices</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {knowledgeBases.filter(kb => kb.status === 'active').length}
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
              {knowledgeBases.map((kb) => (
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
                  <TableCell>{kb.documentCount.toLocaleString()}</TableCell>
                  <TableCell>{getStatusBadge(kb.status)}</TableCell>
                  <TableCell>{new Date(kb.lastUpdated).toLocaleDateString()}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="icon">
                        <Upload className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon">
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon">
                        <Settings className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon">
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
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
