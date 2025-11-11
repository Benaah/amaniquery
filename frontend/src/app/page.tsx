import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Brain,
  Scale,
  Newspaper,
  Github,
  Star,
  GitFork,
  ExternalLink,
  Sparkles,
  Shield,
  Users,
  MessageSquare,
  Database,
  Zap
} from "lucide-react"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-accent/10 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-20 left-10 w-72 h-72 bg-primary/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-40 right-20 w-96 h-96 bg-accent/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-20 left-1/3 w-80 h-80 bg-secondary/20 rounded-full blur-3xl animate-pulse delay-500"></div>
        <div className="absolute bottom-40 right-10 w-64 h-64 bg-primary/15 rounded-full blur-3xl animate-pulse delay-1500"></div>
      </div>

      {/* Floating Icons */}
      <div className="absolute inset-0 pointer-events-none">
        <Brain className="absolute top-32 left-20 w-8 h-8 text-primary/40 animate-bounce" style={{animationDelay: '0s'}} />
        <Scale className="absolute top-48 right-32 w-6 h-6 text-accent/40 animate-bounce" style={{animationDelay: '1s'}} />
        <Newspaper className="absolute bottom-64 left-16 w-7 h-7 text-primary/30 animate-bounce" style={{animationDelay: '2s'}} />
        <Shield className="absolute bottom-32 right-24 w-8 h-8 text-accent/40 animate-bounce" style={{animationDelay: '0.5s'}} />
        <Database className="absolute top-64 left-1/2 w-6 h-6 text-primary/35 animate-bounce" style={{animationDelay: '1.5s'}} />
        <MessageSquare className="absolute bottom-48 right-1/3 w-7 h-7 text-accent/35 animate-bounce" style={{animationDelay: '2.5s'}} />
      </div>

      <div className="relative z-10">
        {/* Header */}
        <header className="border-b bg-background/80 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center space-x-2">
                <Brain className="w-8 h-8 text-primary" />
                <span className="text-2xl font-bold">AmaniQuery</span>
              </div>
              <div className="flex items-center space-x-4">
                <Link href="/chat">
                  <Button variant="outline" size="sm">
                    Try Chat
                  </Button>
                </Link>
                <Link href="/admin">
                  <Button variant="outline" size="sm">
                    Admin
                  </Button>
                </Link>
                <a
                  href="https://github.com/Benaah/amaniquery"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1 text-muted-foreground hover:text-foreground transition-colors"
                >
                  <Github className="w-4 h-4" />
                  <span className="hidden sm:inline">GitHub</span>
                </a>
              </div>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto text-center">
            <div className="mb-8">
              <Badge variant="secondary" className="mb-4">
                <Sparkles className="w-3 h-3 mr-1" />
                AI-Powered Legal Intelligence
              </Badge>
              <h1 className="text-4xl sm:text-6xl font-bold mb-6 bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent animate-gradient-x">
                Kenya&apos;s AI Legal Assistant
              </h1>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
                Experience the future of legal research with AmaniQuery - an intelligent RAG system
                that combines constitutional law, parliamentary proceedings, and news analysis
                to provide accurate, verifiable answers about Kenyan governance.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
              <Link href="/chat">
                <Button size="lg" className="text-lg px-8 py-3">
                  <MessageSquare className="w-5 h-5 mr-2" />
                  Start Chatting
                </Button>
              </Link>
              <a
                href="https://github.com/Benaah/amaniquery"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="outline" size="lg" className="text-lg px-8 py-3">
                  <Github className="w-5 h-5 mr-2" />
                  View on GitHub
                </Button>
              </a>
            </div>

            {/* Feature Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20">
                <CardHeader>
                  <Scale className="w-10 h-10 text-primary mb-2" />
                  <CardTitle>Constitutional Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Deep analysis of Kenyan constitutional law with AI-powered alignment checking
                    between bills and the supreme law.
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur-sm border-accent/20">
                <CardHeader>
                  <Newspaper className="w-10 h-10 text-accent mb-2" />
                  <CardTitle>Parliamentary Intelligence</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Real-time access to parliamentary proceedings, bills, and debates
                    with intelligent summarization and insights.
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur-sm border-primary/20">
                <CardHeader>
                  <Shield className="w-10 h-10 text-primary mb-2" />
                  <CardTitle>Verified Sources</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Every answer backed by verifiable sources from official government
                    publications and reputable news outlets.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* AI Integration Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-primary/5 via-accent/5 to-primary/5">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">
                AI Integration Across Legal Domains
              </h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
                AmaniQuery seamlessly integrates AI across multiple aspects of legal research,
                governance, and public information access.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <div className="space-y-8">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                    <Brain className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold mb-2">Intelligent Document Processing</h3>
                    <p className="text-muted-foreground">
                      Advanced NLP models process legal documents, extracting key provisions,
                      analyzing sentiment, and identifying relationships between laws.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center">
                    <Database className="w-6 h-6 text-accent" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold mb-2">Vector Database Integration</h3>
                    <p className="text-muted-foreground">
                      Semantic search capabilities powered by vector embeddings for
                      precise retrieval of relevant legal information.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                    <MessageSquare className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold mb-2">Conversational AI</h3>
                    <p className="text-muted-foreground">
                      Natural language interface for querying complex legal topics
                      with contextual follow-up and clarification capabilities.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center">
                    <Shield className="w-6 h-6 text-accent" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold mb-2">Constitutional Alignment</h3>
                    <p className="text-muted-foreground">
                      Specialized analysis comparing proposed legislation with
                      constitutional provisions for compliance verification.
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative">
                <div className="bg-gradient-to-br from-primary/20 via-accent/10 to-primary/20 rounded-2xl p-8 backdrop-blur-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-card/50 rounded-lg p-4 text-center">
                      <Scale className="w-8 h-8 text-primary mx-auto mb-2" />
                      <h4 className="font-semibold">Constitution</h4>
                      <p className="text-sm text-muted-foreground">Supreme Law</p>
                    </div>
                    <div className="bg-card/50 rounded-lg p-4 text-center">
                      <Newspaper className="w-8 h-8 text-accent mx-auto mb-2" />
                      <h4 className="font-semibold">Parliament</h4>
                      <p className="text-sm text-muted-foreground">Live Debates</p>
                    </div>
                    <div className="bg-card/50 rounded-lg p-4 text-center">
                      <Shield className="w-8 h-8 text-primary mx-auto mb-2" />
                      <h4 className="font-semibold">Bills</h4>
                      <p className="text-sm text-muted-foreground">Legislation</p>
                    </div>
                    <div className="bg-card/50 rounded-lg p-4 text-center">
                      <Users className="w-8 h-8 text-accent mx-auto mb-2" />
                      <h4 className="font-semibold">Public</h4>
                      <p className="text-sm text-muted-foreground">Sentiment</p>
                    </div>
                  </div>
                  <div className="mt-6 text-center">
                    <Zap className="w-12 h-12 text-primary mx-auto mb-2" />
                    <p className="text-sm font-medium">AI-Powered Integration</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* GitHub Contributions Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto text-center">
            <div className="mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">
                Join the Open Source Movement
              </h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
                AmaniQuery is an open-source project dedicated to democratizing access to legal information
                in Kenya. Your contributions can help build a more transparent and accessible legal system.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
              <Card className="bg-card/50 backdrop-blur-sm">
                <CardHeader>
                  <Star className="w-10 h-10 text-primary mx-auto mb-2" />
                  <CardTitle>Contribute Code</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground mb-4">
                    Help improve the AI models, add new features, or enhance the user interface.
                  </p>
                  <a
                    href="https://github.com/Benaah/amaniquery/issues"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    View Issues <ExternalLink className="w-3 h-3 inline ml-1" />
                  </a>
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur-sm">
                <CardHeader>
                  <GitFork className="w-10 h-10 text-accent mx-auto mb-2" />
                  <CardTitle>Report Issues</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground mb-4">
                    Found a bug or have a suggestion? Help us improve by reporting issues.
                  </p>
                  <a
                    href="https://github.com/Benaah/amaniquery/issues/new"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent hover:underline"
                  >
                    Report Issue <ExternalLink className="w-3 h-3 inline ml-1" />
                  </a>
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur-sm">
                <CardHeader>
                  <Users className="w-10 h-10 text-primary mx-auto mb-2" />
                  <CardTitle>Community</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground mb-4">
                    Join discussions, share ideas, and connect with fellow contributors.
                  </p>
                  <a
                    href="https://github.com/Benaah/amaniquery/discussions"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    Join Discussion <ExternalLink className="w-3 h-3 inline ml-1" />
                  </a>
                </CardContent>
              </Card>
            </div>

            <div className="bg-gradient-to-r from-primary/10 via-accent/10 to-primary/10 rounded-2xl p-8 backdrop-blur-sm">
              <h3 className="text-2xl font-bold mb-4">Ready to Contribute?</h3>
              <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
                Whether you&apos;re a developer, legal expert, or AI enthusiast, your contributions
                can make a real difference in improving access to legal information in Kenya.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <a
                  href="https://github.com/Benaah/amaniquery"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button size="lg" className="px-8">
                    <Github className="w-5 h-5 mr-2" />
                    Fork on GitHub
                  </Button>
                </a>
                <a
                  href="https://github.com/Benaah/amaniquery/blob/master/CONTRIBUTING.md"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="outline" size="lg" className="px-8">
                    <ExternalLink className="w-5 h-5 mr-2" />
                    Contributing Guide
                  </Button>
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t bg-background/80 backdrop-blur-sm py-8 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <Brain className="w-6 h-6 text-primary" />
              <span className="text-lg font-semibold">AmaniQuery</span>
            </div>
            <p className="text-muted-foreground mb-4">
              Democratizing access to legal information through AI-powered intelligence.
            </p>
            <div className="flex justify-center space-x-6">
              <a
                href="https://github.com/Benaah/amaniquery"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <Github className="w-5 h-5" />
              </a>
              <Link href="/chat" className="text-muted-foreground hover:text-foreground transition-colors">
                <MessageSquare className="w-5 h-5" />
              </Link>
              <Link href="/admin" className="text-muted-foreground hover:text-foreground transition-colors">
                <Shield className="w-5 h-5" />
              </Link>
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              © 2025 AmaniQuery. Open source under MIT License.
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}
