"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { BlogPostCard } from "@/components/blog-post-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import {
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  Newspaper,
  Megaphone,
  RefreshCw,
} from "lucide-react"
import Link from "next/link"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface BlogPost {
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

interface BlogResponse {
  posts: BlogPost[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

interface Category {
  id: string
  name: string
  slug: string
}

interface Tag {
  id: string
  name: string
  slug: string
}

function BlogList() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [posts, setPosts] = useState<BlogPost[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [tags, setTags] = useState<Tag[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState(searchParams.get("search") || "")
  const [selectedPostType, setSelectedPostType] = useState<string | null>(
    searchParams.get("post_type") || null
  )
  const [selectedCategory, setSelectedCategory] = useState<string | null>(
    searchParams.get("category") || null
  )
  const [selectedTag, setSelectedTag] = useState<string | null>(
    searchParams.get("tag") || null
  )
  const [currentPage, setCurrentPage] = useState(
    parseInt(searchParams.get("page") || "1")
  )
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    page_size: 10,
    total_pages: 1,
  })

  const fetchPosts = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append("page", currentPage.toString())
      params.append("page_size", "10")
      if (selectedPostType) params.append("post_type", selectedPostType)
      if (selectedCategory) params.append("category_slug", selectedCategory)
      if (selectedTag) params.append("tag_slug", selectedTag)
      if (searchQuery) params.append("search", searchQuery)

      const response = await fetch(`${API_BASE_URL}/api/v1/blog/posts?${params}`)
      if (response.ok) {
        const data: BlogResponse = await response.json()
        setPosts(data.posts)
        setPagination({
          total: data.total,
          page: data.page,
          page_size: data.page_size,
          total_pages: data.total_pages,
        })
      }
    } catch (error) {
      console.error("Failed to fetch posts:", error)
    } finally {
      setLoading(false)
    }
  }

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/categories`)
      if (response.ok) {
        const data: Category[] = await response.json()
        setCategories(data)
      }
    } catch (error) {
      console.error("Failed to fetch categories:", error)
    }
  }

  const fetchTags = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/tags`)
      if (response.ok) {
        const data: Tag[] = await response.json()
        setTags(data)
      }
    } catch (error) {
      console.error("Failed to fetch tags:", error)
    }
  }

  useEffect(() => {
    fetchCategories()
    fetchTags()
  }, [])

  useEffect(() => {
    fetchPosts()
  }, [currentPage, selectedPostType, selectedCategory, selectedTag, searchQuery])

  useEffect(() => {
    // Update URL with current filters
    const params = new URLSearchParams()
    if (selectedPostType) params.append("post_type", selectedPostType)
    if (selectedCategory) params.append("category", selectedCategory)
    if (selectedTag) params.append("tag", selectedTag)
    if (searchQuery) params.append("search", searchQuery)
    if (currentPage > 1) params.append("page", currentPage.toString())

    router.push(`/blog?${params.toString()}`, { scroll: false })
  }, [selectedPostType, selectedCategory, selectedTag, searchQuery, currentPage, router])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setCurrentPage(1)
    fetchPosts()
  }

  const clearFilters = () => {
    setSelectedPostType(null)
    setSelectedCategory(null)
    setSelectedTag(null)
    setSearchQuery("")
    setCurrentPage(1)
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold mb-2">Blog</h1>
              <p className="text-muted-foreground">
                News, announcements, and updates from AmaniQuery
              </p>
            </div>
            <Link href="/">
              <Button variant="outline">Back to Home</Button>
            </Link>
          </div>

          {/* Search */}
          <form onSubmit={handleSearch} className="mb-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                  type="text"
                  placeholder="Search posts..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button type="submit">Search</Button>
            </div>
          </form>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Filters */}
          <div className="lg:col-span-1">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold flex items-center">
                    <Filter className="w-4 h-4 mr-2" />
                    Filters
                  </h2>
                  {(selectedPostType || selectedCategory || selectedTag) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearFilters}
                      className="text-xs"
                    >
                      Clear
                    </Button>
                  )}
                </div>

                {/* Post Type Filter */}
                <div className="mb-4">
                  <h3 className="text-sm font-medium mb-2">Post Type</h3>
                  <div className="space-y-2">
                    {["news", "announcement", "update"].map((type) => (
                      <button
                        key={type}
                        onClick={() => {
                          setSelectedPostType(
                            selectedPostType === type ? null : type
                          )
                          setCurrentPage(1)
                        }}
                        className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                          selectedPostType === type
                            ? "bg-primary text-primary-foreground"
                            : "hover:bg-accent"
                        }`}
                      >
                        <div className="flex items-center">
                          {type === "news" && <Newspaper className="w-4 h-4 mr-2" />}
                          {type === "announcement" && (
                            <Megaphone className="w-4 h-4 mr-2" />
                          )}
                          {type === "update" && (
                            <RefreshCw className="w-4 h-4 mr-2" />
                          )}
                          {type.charAt(0).toUpperCase() + type.slice(1)}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Categories Filter */}
                {categories.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium mb-2">Categories</h3>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {categories.map((category) => (
                        <button
                          key={category.id}
                          onClick={() => {
                            setSelectedCategory(
                              selectedCategory === category.slug ? null : category.slug
                            )
                            setCurrentPage(1)
                          }}
                          className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                            selectedCategory === category.slug
                              ? "bg-primary text-primary-foreground"
                              : "hover:bg-accent"
                          }`}
                        >
                          {category.name}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tags Filter */}
                {tags.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium mb-2">Tags</h3>
                    <div className="flex flex-wrap gap-2">
                      {tags.map((tag) => (
                        <Badge
                          key={tag.id}
                          variant={
                            selectedTag === tag.slug ? "default" : "outline"
                          }
                          className="cursor-pointer"
                          onClick={() => {
                            setSelectedTag(
                              selectedTag === tag.slug ? null : tag.slug
                            )
                            setCurrentPage(1)
                          }}
                        >
                          {tag.name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : posts.length === 0 ? (
              <Card>
                <CardContent className="p-12 text-center">
                  <p className="text-muted-foreground">
                    No posts found. Try adjusting your filters.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                  {posts.map((post) => (
                    <BlogPostCard key={post.id} post={post} />
                  ))}
                </div>

                {/* Pagination */}
                {pagination.total_pages > 1 && (
                  <div className="flex items-center justify-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="w-4 h-4" />
                      Previous
                    </Button>
                    <span className="text-sm text-muted-foreground">
                      Page {pagination.page} of {pagination.total_pages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setCurrentPage((p) =>
                          Math.min(pagination.total_pages, p + 1)
                        )
                      }
                      disabled={currentPage === pagination.total_pages}
                    >
                      Next
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function BlogPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    }>
      <BlogList />
    </Suspense>
  )
}
