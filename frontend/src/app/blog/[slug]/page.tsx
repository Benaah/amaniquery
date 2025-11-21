"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Calendar, User, ArrowLeft, Share2 } from "lucide-react"
import Image from "next/image"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface BlogPost {
  id: string
  title: string
  slug: string
  markdown_content?: string
  html_content?: string
  excerpt?: string
  post_type: string
  featured_image_url?: string
  author: {
    id: string
    name?: string
    email: string
    profile_image_url?: string
  }
  categories: Array<{ id: string; name: string; slug: string }>
  tags: Array<{ id: string; name: string; slug: string }>
  published_at?: string
  created_at: string
  updated_at: string
}

export default function BlogPostPage() {
  const params = useParams()
  const router = useRouter()
  const slug = params.slug as string
  const [post, setPost] = useState<BlogPost | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPost = async () => {
      setLoading(true)
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/blog/posts/${slug}`)
        if (response.ok) {
          const data: BlogPost = await response.json()
          setPost(data)
        } else if (response.status === 404) {
          router.push("/blog")
        }
      } catch (error) {
        console.error("Failed to fetch post:", error)
      } finally {
        setLoading(false)
      }
    }

    if (slug) {
      fetchPost()
    }
  }, [slug, router])

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  const getPostTypeColor = (type: string) => {
    switch (type) {
      case "news":
        return "bg-blue-500/10 text-blue-500"
      case "announcement":
        return "bg-yellow-500/10 text-yellow-500"
      case "update":
        return "bg-green-500/10 text-green-500"
      default:
        return "bg-gray-500/10 text-gray-500"
    }
  }

  const handleShare = async () => {
    if (navigator.share && post) {
      try {
        await navigator.share({
          title: post.title,
          text: post.excerpt || "",
          url: window.location.href,
        })
      } catch (error) {
        // User cancelled or error occurred
        console.log("Share cancelled or failed")
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href)
      alert("Link copied to clipboard!")
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!post) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground mb-4">Post not found</p>
            <Link href="/blog">
              <Button>Back to Blog</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Button */}
        <Link href="/blog">
          <Button variant="ghost" className="mb-6">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Blog
          </Button>
        </Link>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Badge className={getPostTypeColor(post.post_type)}>
              {post.post_type}
            </Badge>
            {post.published_at && (
              <div className="flex items-center text-sm text-muted-foreground">
                <Calendar className="w-4 h-4 mr-1" />
                {formatDate(post.published_at)}
              </div>
            )}
          </div>
          <h1 className="text-4xl font-bold mb-4">{post.title}</h1>
          {post.excerpt && (
            <p className="text-xl text-muted-foreground mb-6">{post.excerpt}</p>
          )}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center text-sm text-muted-foreground">
                <User className="w-4 h-4 mr-1" />
                <span>{post.author.name || post.author.email}</span>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={handleShare}>
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </Button>
          </div>
        </div>

        {/* Featured Image */}
        {post.featured_image_url && (
          <div className="relative w-full h-96 mb-8 rounded-lg overflow-hidden">
            <Image
              src={post.featured_image_url}
              alt={post.title}
              fill
              className="object-cover"
            />
          </div>
        )}

        {/* Content */}
        <article className="prose prose-lg dark:prose-invert max-w-none mb-8">
          {post.html_content ? (
            <div dangerouslySetInnerHTML={{ __html: post.html_content }} />
          ) : post.markdown_content ? (
            <div className="whitespace-pre-wrap">{post.markdown_content}</div>
          ) : (
            <p className="text-muted-foreground">No content available.</p>
          )}
        </article>

        {/* Categories and Tags */}
        {(post.categories.length > 0 || post.tags.length > 0) && (
          <Card className="mb-8">
            <CardContent className="p-6">
              {post.categories.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold mb-2">Categories</h3>
                  <div className="flex flex-wrap gap-2">
                    {post.categories.map((category) => (
                      <Badge key={category.id} variant="outline">
                        {category.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {post.tags.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {post.tags.map((tag) => (
                      <Badge key={tag.id} variant="secondary">
                        {tag.name}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Navigation */}
        <div className="flex justify-between items-center pt-8 border-t">
          <Link href="/blog">
            <Button variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              All Posts
            </Button>
          </Link>
          <Link href="/">
            <Button variant="ghost">Back to Home</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}

