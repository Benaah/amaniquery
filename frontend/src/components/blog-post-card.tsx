"use client"

import Link from "next/link"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Calendar, User, ArrowRight } from "lucide-react"
import Image from "next/image"

interface BlogPostCardProps {
  post: {
    id: string
    title: string
    slug: string
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
  }
}

export function BlogPostCard({ post }: BlogPostCardProps) {
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

  return (
    <Link href={`/blog/${post.slug}`}>
      <Card className="h-full hover:shadow-lg transition-shadow duration-200 cursor-pointer group">
        {post.featured_image_url && (
          <div className="relative w-full h-48 overflow-hidden rounded-t-lg">
            <Image
              src={post.featured_image_url}
              alt={post.title}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-200"
            />
          </div>
        )}
        <CardHeader>
          <div className="flex items-center justify-between mb-2">
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
          <h3 className="text-xl font-semibold group-hover:text-primary transition-colors line-clamp-2">
            {post.title}
          </h3>
        </CardHeader>
        <CardContent>
          {post.excerpt && (
            <p className="text-muted-foreground mb-4 line-clamp-3">
              {post.excerpt}
            </p>
          )}
          <div className="flex items-center justify-between">
            <div className="flex items-center text-sm text-muted-foreground">
              <User className="w-4 h-4 mr-1" />
              <span>{post.author.name || post.author.email}</span>
            </div>
            <div className="flex items-center text-primary group-hover:translate-x-1 transition-transform">
              Read more
              <ArrowRight className="w-4 h-4 ml-1" />
            </div>
          </div>
          {(post.categories.length > 0 || post.tags.length > 0) && (
            <div className="mt-4 flex flex-wrap gap-2">
              {post.categories.slice(0, 2).map((category) => (
                <Badge key={category.id} variant="outline" className="text-xs">
                  {category.name}
                </Badge>
              ))}
              {post.tags.slice(0, 3).map((tag) => (
                <Badge key={tag.id} variant="secondary" className="text-xs">
                  {tag.name}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  )
}

