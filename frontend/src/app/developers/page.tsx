"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Code,
  Book,
  Key,
  Globe,
  Zap,
  Shield,
  Database,
  Webhook,
  FileText,
  ExternalLink,
  Copy,
  Check,
  ArrowLeft,
} from "lucide-react"
import { AnimatedIDE } from "@/components/animated-ide"
import { ChatStreamDemo } from "@/components/chat-stream-demo"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface ApiEndpoint {
  method: string
  path: string
  description: string
  auth: boolean
  category: string
}

const apiEndpoints: ApiEndpoint[] = [
  {
    method: "POST",
    path: "/query",
    description: "General RAG query with filters",
    auth: false,
    category: "Core",
  },
  {
    method: "POST",
    path: "/query/stream",
    description: "Streaming RAG query (token-by-token)",
    auth: false,
    category: "Core",
  },
  {
    method: "POST",
    path: "/alignment-check",
    description: "Full constitutional alignment analysis",
    auth: false,
    category: "Legal",
  },
  {
    method: "GET",
    path: "/api/v1/blog/posts",
    description: "List published blog posts",
    auth: false,
    category: "Blog",
  },
  {
    method: "GET",
    path: "/api/v1/blog/posts/{slug}",
    description: "Get blog post by slug",
    auth: false,
    category: "Blog",
  },
  {
    method: "POST",
    path: "/api/v1/blog/posts",
    description: "Create blog post (admin)",
    auth: true,
    category: "Blog",
  },
  {
    method: "GET",
    path: "/api/v1/auth/me",
    description: "Get current user profile",
    auth: true,
    category: "Auth",
  },
  {
    method: "POST",
    path: "/api/v1/auth/integrations",
    description: "Create third-party integration",
    auth: true,
    category: "Auth",
  },
  {
    method: "POST",
    path: "/api/v1/auth/integrations/{id}/keys",
    description: "Create API key",
    auth: true,
    category: "Auth",
  },
]

const codeExamples = {
  python: `import requests

# Query the API
response = requests.post(
    "${API_BASE_URL}/query",
    json={
        "query": "What are the recent parliamentary debates on finance?",
        "top_k": 5,
        "category": "Parliament"
    }
)

data = response.json()
print(data["answer"])`,

  javascript: `// Using fetch API
const response = await fetch('${API_BASE_URL}/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'What are the recent parliamentary debates on finance?',
    top_k: 5,
    category: 'Parliament'
  })
});

const data = await response.json();
console.log(data.answer);`,

  curl: `curl -X POST ${API_BASE_URL}/query \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "What are the recent parliamentary debates on finance?",
    "top_k": 5,
    "category": "Parliament"
  }'`,
}

export default function DevelopersPage() {
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  const [selectedLanguage, setSelectedLanguage] = useState<"python" | "javascript" | "curl">("python")

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCode(id)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  const getMethodColor = (method: string) => {
    switch (method) {
      case "GET":
        return "bg-blue-500/10 text-blue-500"
      case "POST":
        return "bg-green-500/10 text-green-500"
      case "PUT":
        return "bg-yellow-500/10 text-yellow-500"
      case "DELETE":
        return "bg-red-500/10 text-red-500"
      default:
        return "bg-gray-500/10 text-gray-500"
    }
  }

  const categories = Array.from(new Set(apiEndpoints.map((e) => e.category)))

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link href="/">
            <Button variant="ghost" className="mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">Developer Documentation</h1>
              <p className="text-muted-foreground text-lg">
                Integrate AmaniQuery into your applications with our comprehensive API
              </p>
            </div>
            <div className="flex gap-2">
              <a href={`${API_BASE_URL}/docs`} target="_blank" rel="noopener noreferrer">
                <Button variant="outline">
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Swagger UI
                </Button>
              </a>
              <a href={`${API_BASE_URL}/redoc`} target="_blank" rel="noopener noreferrer">
                <Button variant="outline">
                  <ExternalLink className="w-4 h-4 mr-2" />
                  ReDoc
                </Button>
              </a>
            </div>
          </div>
        </div>

        {/* Interactive Demos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <AnimatedIDE />
          <ChatStreamDemo />
        </div>

        {/* Quick Start */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Zap className="w-5 h-5 mr-2" />
              Quick Start
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2">1. Get API Access</h3>
              <p className="text-muted-foreground mb-4">
                Sign up for an account and create an API key from your dashboard.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">2. Make Your First Request</h3>
              <div className="flex gap-2 mb-4">
                {(["python", "javascript", "curl"] as const).map((lang) => (
                  <Button
                    key={lang}
                    variant={selectedLanguage === lang ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSelectedLanguage(lang)}
                  >
                    {lang === "python" ? "Python" : lang === "javascript" ? "JavaScript" : "cURL"}
                  </Button>
                ))}
              </div>
              <div className="relative">
                <pre className="bg-muted p-4 rounded-lg overflow-x-auto">
                  <code>{codeExamples[selectedLanguage]}</code>
                </pre>
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute top-2 right-2"
                  onClick={() => copyToClipboard(codeExamples[selectedLanguage], "quickstart")}
                >
                  {copiedCode === "quickstart" ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* API Endpoints */}
            <div>
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <Code className="w-6 h-6 mr-2" />
                API Endpoints
              </h2>
              <div className="space-y-6">
                {categories.map((category) => {
                  const endpoints = apiEndpoints.filter((e) => e.category === category)
                  return (
                    <Card key={category}>
                      <CardHeader>
                        <CardTitle>{category}</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {endpoints.map((endpoint, idx) => (
                          <div
                            key={idx}
                            className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <Badge className={getMethodColor(endpoint.method)}>
                                  {endpoint.method}
                                </Badge>
                                <code className="text-sm font-mono">{endpoint.path}</code>
                              </div>
                              {endpoint.auth && (
                                <Badge variant="outline" className="text-xs">
                                  <Key className="w-3 h-3 mr-1" />
                                  Auth Required
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">{endpoint.description}</p>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            </div>

            {/* Authentication */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Shield className="w-5 h-5 mr-2" />
                  Authentication
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">API Keys</h3>
                  <p className="text-muted-foreground mb-4">
                    Create API keys from your dashboard for programmatic access. Include the key in
                    the <code className="bg-muted px-1 rounded">X-API-Key</code> header.
                  </p>
                  <div className="bg-muted p-4 rounded-lg">
                    <code className="text-sm">
                      X-API-Key: your-api-key-here
                    </code>
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">OAuth 2.0</h3>
                  <p className="text-muted-foreground mb-4">
                    For third-party integrations, use OAuth 2.0 for secure authentication. Create an
                    OAuth client from your dashboard.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Session Tokens</h3>
                  <p className="text-muted-foreground">
                    For web applications, use session tokens obtained after login. Include in the{" "}
                    <code className="bg-muted px-1 rounded">X-Session-Token</code> header or as a
                    cookie.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Rate Limiting */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Zap className="w-5 h-5 mr-2" />
                  Rate Limiting
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  API requests are rate-limited to ensure fair usage:
                </p>
                <ul className="list-disc list-inside space-y-2 text-muted-foreground">
                  <li>Free tier: 60 requests per minute, 1000 per hour</li>
                  <li>Pro tier: 300 requests per minute, 10,000 per hour</li>
                  <li>Enterprise: Custom limits</li>
                </ul>
                <p className="text-sm text-muted-foreground mt-4">
                  Rate limit headers are included in all responses:
                </p>
                <div className="bg-muted p-4 rounded-lg mt-2">
                  <code className="text-sm">
                    X-RateLimit-Remaining: 59<br />
                    X-RateLimit-Reset: 1640995200
                  </code>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Resources */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Book className="w-5 h-5 mr-2" />
                  Resources
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <a
                  href={`${API_BASE_URL}/docs`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center text-primary hover:underline"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  Interactive API Docs
                </a>
                <a
                  href="https://github.com/Benaah/amaniquery"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center text-primary hover:underline"
                >
                  <Code className="w-4 h-4 mr-2" />
                  GitHub Repository
                </a>
                <Link href="/blog" className="flex items-center text-primary hover:underline">
                  <FileText className="w-4 h-4 mr-2" />
                  Blog & Updates
                </Link>
              </CardContent>
            </Card>

            {/* Features */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Database className="w-5 h-5 mr-2" />
                  Features
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <div className="flex items-center">
                  <Check className="w-4 h-4 mr-2 text-green-500" />
                  RAG-powered queries
                </div>
                <div className="flex items-center">
                  <Check className="w-4 h-4 mr-2 text-green-500" />
                  Constitutional alignment
                </div>
                <div className="flex items-center">
                  <Check className="w-4 h-4 mr-2 text-green-500" />
                  Streaming responses
                </div>
                <div className="flex items-center">
                  <Check className="w-4 h-4 mr-2 text-green-500" />
                  Blog API
                </div>
                <div className="flex items-center">
                  <Check className="w-4 h-4 mr-2 text-green-500" />
                  OAuth 2.0 support
                </div>
                <div className="flex items-center">
                  <Check className="w-4 h-4 mr-2 text-green-500" />
                  Webhook support
                </div>
              </CardContent>
            </Card>

            {/* Support */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Globe className="w-5 h-5 mr-2" />
                  Support
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <a
                  href="https://github.com/Benaah/amaniquery/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center text-primary hover:underline text-sm"
                >
                  Report Issues
                </a>
                <a
                  href="https://github.com/Benaah/amaniquery/discussions"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center text-primary hover:underline text-sm"
                >
                  Community Discussions
                </a>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

