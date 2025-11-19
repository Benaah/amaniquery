"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/lib/auth-context"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ThemeToggle } from "@/components/theme-toggle"
import NotificationSubscriptionDialog from "@/components/NotificationSubscriptionDialog"
import {
  Brain,
  Scale,
  Newspaper,
  Github,
  Star,
  GitFork,
  ExternalLink,
  Sparkles,
  Users,
  Database,
  MessageSquare,
  Shield,
  Zap,
  Bell
} from "lucide-react"

export default function LandingPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const { isAuthenticated, isAdmin, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && isAuthenticated) {
      // Redirect authenticated users based on role
      if (isAdmin) {
        router.push("/admin")
      } else {
        router.push("/chat")
      }
    }
  }, [isAuthenticated, isAdmin, loading, router])

  // Show loading state while checking auth
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

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
            <div className="flex justify-between items-center py-3 md:py-4">
              <div className="flex items-center space-x-2">
                <Brain className="w-6 h-6 md:w-8 md:h-8 text-primary" />
                <span className="text-lg md:text-2xl font-bold">AmaniQuery</span>
              </div>
              <div className="flex items-center space-x-2 md:space-x-4">
                <ThemeToggle />
                <a
                  href="https://github.com/Benaah/amaniquery"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1 text-muted-foreground hover:text-foreground transition-colors"
                >
                  <Github className="w-3 h-3 md:w-4 md:h-4" />
                  <span className="hidden sm:inline text-xs md:text-sm">GitHub</span>
                </a>
              </div>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <section className="py-12 md:py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto text-center">
            <div className="mb-6 md:mb-8">
              <Badge variant="secondary" className="mb-3 md:mb-4 text-xs md:text-sm">
                <Sparkles className="w-3 h-3 mr-1" />
                AI-Powered Legal Intelligence
              </Badge>
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-4 md:mb-6 bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent animate-gradient-x leading-tight">
                Kenya&apos;s AI Legal Assistant
              </h1>
              <p className="text-base md:text-lg lg:text-xl text-muted-foreground max-w-3xl mx-auto mb-6 md:mb-8 px-2">
                Experience the future of legal research with AmaniQuery - an intelligent RAG system
                that combines constitutional law, parliamentary proceedings, and news analysis
                to provide accurate, verifiable answers about Kenyan governance.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 md:gap-4 justify-center mb-12 md:mb-16 px-4">
              <Link href="/chat">
                <Button size="lg" className="text-base md:text-lg px-6 md:px-8 py-3 md:py-3 w-full sm:w-auto min-h-[44px]">
                  <MessageSquare className="w-4 h-4 md:w-5 md:h-5 mr-2" />
                  Start Chatting
                </Button>
              </Link>
              <a
                href="https://github.com/Benaah/amaniquery"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="outline" size="lg" className="text-base md:text-lg px-6 md:px-8 py-3 md:py-3 w-full sm:w-auto min-h-[44px]">
                  <Github className="w-4 h-4 md:w-5 md:h-5 mr-2" />
                  View on GitHub
                </Button>
              </a>
            </div>

            {/* Feature Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 max-w-5xl mx-auto px-2">
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20">
                <CardHeader className="pb-3">
                  <Scale className="w-8 h-8 md:w-10 md:h-10 text-primary mb-2" />
                  <CardTitle className="text-base md:text-lg">Constitutional Analysis</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm md:text-base text-muted-foreground">
                    Deep analysis of Kenyan constitutional law with AI-powered alignment checking
                    between bills and the supreme law.
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur-sm border-accent/20">
                <CardHeader className="pb-3">
                  <Newspaper className="w-8 h-8 md:w-10 md:h-10 text-accent mb-2" />
                  <CardTitle className="text-base md:text-lg">Parliamentary Intelligence</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm md:text-base text-muted-foreground">
                    Real-time access to parliamentary proceedings, bills, and debates
                    with intelligent summarization and insights.
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur-sm border-primary/20">
                <CardHeader className="pb-3">
                  <Shield className="w-8 h-8 md:w-10 md:h-10 text-primary mb-2" />
                  <CardTitle className="text-base md:text-lg">Verified Sources</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm md:text-base text-muted-foreground">
                    Every answer backed by verifiable sources from official government
                    publications and reputable news outlets.
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* News Notifications Section */}
            <div className="mt-12 md:mt-16">
              <Card className="bg-card/50 backdrop-blur-sm border-accent/20 max-w-2xl mx-auto">
                <CardHeader>
                  <CardTitle className="flex items-center justify-center text-lg md:text-xl">
                    <Bell className="w-5 h-5 md:w-6 md:h-6 mr-2 text-accent" />
                    Stay Updated with News Notifications
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-center">
                  <p className="text-sm md:text-base text-muted-foreground mb-4 md:mb-6">
                    Get instant notifications via WhatsApp or SMS when new articles are published.
                    Choose your preferred categories and sources to stay informed.
                  </p>
                  <Button
                    size="lg"
                    onClick={() => setIsDialogOpen(true)}
                    className="min-h-[44px] px-6 md:px-8"
                  >
                    <Bell className="w-4 h-4 md:w-5 md:h-5 mr-2" />
                    Subscribe to Notifications
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* AI Integration Section */}
        <section className="py-12 md:py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-primary/5 via-accent/5 to-primary/5">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-12 md:mb-16">
              <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 md:mb-4">
                AI Integration Across Legal Domains
              </h2>
              <p className="text-base md:text-lg lg:text-xl text-muted-foreground max-w-3xl mx-auto px-2">
                AmaniQuery seamlessly integrates AI across multiple aspects of legal research,
                governance, and public information access.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-12 items-center">
              <div className="space-y-6 md:space-y-8">
                <div className="flex items-start space-x-3 md:space-x-4">
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Brain className="w-5 h-5 md:w-6 md:h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-lg md:text-xl font-semibold mb-2">Intelligent Document Processing</h3>
                    <p className="text-sm md:text-base text-muted-foreground">
                      Advanced NLP models process legal documents, extracting key provisions,
                      analyzing sentiment, and identifying relationships between laws.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3 md:space-x-4">
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-accent/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Database className="w-5 h-5 md:w-6 md:h-6 text-accent" />
                  </div>
                  <div>
                    <h3 className="text-lg md:text-xl font-semibold mb-2">Vector Database Integration</h3>
                    <p className="text-sm md:text-base text-muted-foreground">
                      Semantic search capabilities powered by vector embeddings for
                      precise retrieval of relevant legal information.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3 md:space-x-4">
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <MessageSquare className="w-5 h-5 md:w-6 md:h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-lg md:text-xl font-semibold mb-2">Conversational AI</h3>
                    <p className="text-sm md:text-base text-muted-foreground">
                      Natural language interface for querying complex legal topics
                      with contextual follow-up and clarification capabilities.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3 md:space-x-4">
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-accent/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Shield className="w-5 h-5 md:w-6 md:h-6 text-accent" />
                  </div>
                  <div>
                    <h3 className="text-lg md:text-xl font-semibold mb-2">Constitutional Alignment</h3>
                    <p className="text-sm md:text-base text-muted-foreground">
                      Specialized analysis comparing proposed legislation with
                      constitutional provisions for compliance verification.
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative mt-8 lg:mt-0">
                <div className="bg-gradient-to-br from-primary/20 via-accent/10 to-primary/20 rounded-2xl p-6 md:p-8 backdrop-blur-sm">
                  <div className="grid grid-cols-2 gap-3 md:gap-4">
                    <div className="bg-card/50 rounded-lg p-3 md:p-4 text-center">
                      <Scale className="w-6 h-6 md:w-8 md:h-8 text-primary mx-auto mb-2" />
                      <h4 className="font-semibold text-sm md:text-base">Constitution</h4>
                      <p className="text-xs text-muted-foreground">Supreme Law</p>
                    </div>
                    <div className="bg-card/50 rounded-lg p-3 md:p-4 text-center">
                      <Newspaper className="w-6 h-6 md:w-8 md:h-8 text-accent mx-auto mb-2" />
                      <h4 className="font-semibold text-sm md:text-base">Parliament</h4>
                      <p className="text-xs text-muted-foreground">Live Debates</p>
                    </div>
                    <div className="bg-card/50 rounded-lg p-3 md:p-4 text-center">
                      <Shield className="w-6 h-6 md:w-8 md:h-8 text-primary mx-auto mb-2" />
                      <h4 className="font-semibold text-sm md:text-base">Bills</h4>
                      <p className="text-xs text-muted-foreground">Legislation</p>
                    </div>
                    <div className="bg-card/50 rounded-lg p-3 md:p-4 text-center">
                      <Users className="w-6 h-6 md:w-8 md:h-8 text-accent mx-auto mb-2" />
                      <h4 className="font-semibold text-sm md:text-base">Public</h4>
                      <p className="text-xs text-muted-foreground">Sentiment</p>
                    </div>
                  </div>
                  <div className="mt-4 md:mt-6 text-center">
                    <Zap className="w-8 h-8 md:w-12 md:h-12 text-primary mx-auto mb-2" />
                    <p className="text-xs md:text-sm font-medium">AI-Powered Integration</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* GitHub Contributions Section */}
        <section className="py-12 md:py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto text-center">
            <div className="mb-12 md:mb-16">
              <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 md:mb-4">
                Join the Open Source Movement
              </h2>
              <p className="text-base md:text-lg lg:text-xl text-muted-foreground max-w-3xl mx-auto mb-6 md:mb-8 px-2">
                AmaniQuery is an open-source project dedicated to democratizing access to legal information
                in Kenya. Your contributions can help build a more transparent and accessible legal system.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8 mb-10 md:mb-12">
              <Card className="bg-card/50 backdrop-blur-sm">
                <CardHeader className="pb-3">
                  <Star className="w-8 h-8 md:w-10 md:h-10 text-primary mx-auto mb-2" />
                  <CardTitle className="text-base md:text-lg">Contribute Code</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm md:text-base text-muted-foreground mb-3 md:mb-4">
                    Help improve the AI models, add new features, or enhance the user interface.
                  </p>
                  <a
                    href="https://github.com/Benaah/amaniquery/issues"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline text-sm md:text-base"
                  >
                    View Issues <ExternalLink className="w-3 h-3 inline ml-1" />
                  </a>
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur-sm">
                <CardHeader className="pb-3">
                  <GitFork className="w-8 h-8 md:w-10 md:h-10 text-accent mx-auto mb-2" />
                  <CardTitle className="text-base md:text-lg">Report Issues</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm md:text-base text-muted-foreground mb-3 md:mb-4">
                    Found a bug or have a suggestion? Help us improve by reporting issues.
                  </p>
                  <a
                    href="https://github.com/Benaah/amaniquery/issues/new"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent hover:underline text-sm md:text-base"
                  >
                    Report Issue <ExternalLink className="w-3 h-3 inline ml-1" />
                  </a>
                </CardContent>
              </Card>

              <Card className="bg-card/50 backdrop-blur-sm">
                <CardHeader className="pb-3">
                  <Users className="w-8 h-8 md:w-10 md:h-10 text-primary mx-auto mb-2" />
                  <CardTitle className="text-base md:text-lg">Community</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm md:text-base text-muted-foreground mb-3 md:mb-4">
                    Join discussions, share ideas, and connect with fellow contributors.
                  </p>
                  <a
                    href="https://github.com/Benaah/amaniquery/discussions"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline text-sm md:text-base"
                  >
                    Join Discussion <ExternalLink className="w-3 h-3 inline ml-1" />
                  </a>
                </CardContent>
              </Card>
            </div>

            <div className="bg-gradient-to-r from-primary/10 via-accent/10 to-primary/10 rounded-2xl p-6 md:p-8 backdrop-blur-sm">
              <h3 className="text-xl md:text-2xl font-bold mb-3 md:mb-4">Ready to Contribute?</h3>
              <p className="text-sm md:text-base text-muted-foreground mb-4 md:mb-6 max-w-2xl mx-auto">
                Whether you&apos;re a developer, legal expert, or AI enthusiast, your contributions
                can make a real difference in improving access to legal information in Kenya.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 md:gap-4 justify-center">
                <a
                  href="https://github.com/Benaah/amaniquery"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button size="lg" className="px-6 md:px-8 min-h-[44px] text-sm md:text-base">
                    <Github className="w-4 h-4 md:w-5 md:h-5 mr-2" />
                    Fork on GitHub
                  </Button>
                </a>
                <a
                  href="https://github.com/Benaah/amaniquery/blob/master/CONTRIBUTING.md"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Button variant="outline" size="lg" className="px-6 md:px-8 min-h-[44px] text-sm md:text-base">
                    <ExternalLink className="w-4 h-4 md:w-5 md:h-5 mr-2" />
                    Contributing Guide
                  </Button>
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t bg-background/80 backdrop-blur-sm py-6 md:py-8 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto text-center">
            <div className="flex items-center justify-center space-x-2 mb-3 md:mb-4">
              <Brain className="w-5 h-5 md:w-6 md:h-6 text-primary" />
              <span className="text-base md:text-lg font-semibold">AmaniQuery</span>
            </div>
            <p className="text-sm md:text-base text-muted-foreground mb-3 md:mb-4 px-2">
              Democratizing access to legal information through AI-powered intelligence.
            </p>
            <div className="flex justify-center space-x-4 md:space-x-6">
              <a
                href="https://github.com/Benaah/amaniquery"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <Github className="w-4 h-4 md:w-5 md:h-5" />
              </a>
              <Link href="/chat" className="text-muted-foreground hover:text-foreground transition-colors">
                <MessageSquare className="w-4 h-4 md:w-5 md:h-5" />
              </Link>
              <Link href="/admin" className="text-muted-foreground hover:text-foreground transition-colors">
                <Shield className="w-4 h-4 md:w-5 md:h-5" />
              </Link>
            </div>
            <p className="text-xs md:text-sm text-muted-foreground mt-3 md:mt-4">
              © 2025 AmaniQuery. Open source under MIT License.
            </p>
          </div>
        </footer>
      </div>

      {/* Notification Subscription Dialog */}
      <NotificationSubscriptionDialog
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
      />
    </div>
  )
}
