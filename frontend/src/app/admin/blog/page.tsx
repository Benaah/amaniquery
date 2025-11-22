"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { AdminSidebar } from "@/components/admin-sidebar"
import { ThemeToggle } from "@/components/theme-toggle"
import { BlogEditor } from "@/components/blog-editor"
import { useAuth } from "@/lib/auth-context"
import {
  Plus,
  Edit,
  Trash2,
  Eye,
  Save,
  X,
  Upload,
  FileText,
  Tag,
  Folder,
} from "lucide-react"
import Link from "next/link"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem("session_token")
  const headers: Record<string, string> = {}
  if (token) {
    headers["X-Session-Token"] = token
  }
  return headers
}

/**
 * Removes keys with empty string values from the payload.
 * This ensures optional fields like slug and featured_image_url
 * are not sent as empty strings, which would fail backend validation.
 */
const cleanPostPayload = (payload: Record<string, unknown>): Record<string, unknown> => {
  const cleaned: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(payload)) {
    // Keep the key if it's not an empty string
    // Arrays are always included (even if empty)
    if (value !== "" || Array.isArray(value)) {
      cleaned[key] = value
    }
  }
  return cleaned
}

interface BlogPost {
  id: string
  title: string
  slug: string
  markdown_content?: string
  html_content?: string
  excerpt?: string
  post_type: string
  status: string
  featured_image_url?: string
  author: {
    id: string
    name?: string
    email: string
  }
  categories: Array<{ id: string; name: string; slug: string }>
  tags: Array<{ id: string; name: string; slug: string }>
  published_at?: string
  created_at: string
}

interface Category {
  id: string
  name: string
  slug: string
  description?: string
}

interface Tag {
  id: string
  name: string
  slug: string
}

export default function AdminBlogPage() {
  const { isAuthenticated, isAdmin, loading } = useAuth()
  const router = useRouter()
  const [posts, setPosts] = useState<BlogPost[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [tags, setTags] = useState<Tag[]>([])
  const [loadingData, setLoadingData] = useState(true)
  const [activeTab, setActiveTab] = useState<"posts" | "categories" | "tags">("posts")
  const [editingPost, setEditingPost] = useState<BlogPost | null>(null)
  const [editingCategory, setEditingCategory] = useState<Category | null>(null)
  const [editingTag, setEditingTag] = useState<Tag | null>(null)
  const [showPostForm, setShowPostForm] = useState(false)
  const [postSubmitting, setPostSubmitting] = useState(false) // loading state for create/update

  // Post form state
  const [postForm, setPostForm] = useState({
    title: "",
    slug: "",
    markdown_content: "",
    html_content: "",
    excerpt: "",
    post_type: "news",
    status: "draft",
    featured_image_url: "",
    category_ids: [] as string[],
    tag_ids: [] as string[],
  })

  // Category form state
  const [categoryForm, setCategoryForm] = useState({
    name: "",
    slug: "",
    description: "",
  })

  // Tag form state
  const [tagForm, setTagForm] = useState({
    name: "",
    slug: "",
  })

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/signin?redirect=/admin/blog")
    } else if (!loading && isAuthenticated && !isAdmin) {
      router.push("/chat")
    }
  }, [isAuthenticated, isAdmin, loading, router])

  useEffect(() => {
    if (isAuthenticated && isAdmin) {
      fetchPosts()
      fetchCategories()
      fetchTags()
    }
  }, [isAuthenticated, isAdmin])

  const fetchPosts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/posts?page=1&page_size=100`, {
        headers: getAuthHeaders(),
      })
      if (response.ok) {
        const data = await response.json()
        setPosts(data.posts || [])
      }
    } catch (error) {
      console.error("Failed to fetch posts:", error)
    } finally {
      setLoadingData(false)
    }
  }

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/categories`)
      if (response.ok) {
        const data = await response.json()
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
        const data = await response.json()
        setTags(data)
      }
    } catch (error) {
      console.error("Failed to fetch tags:", error)
    }
  }

  const handleCreatePost = async () => {
    setPostSubmitting(true)
    try {
      const cleanedPayload = cleanPostPayload(postForm)
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/posts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify(cleanedPayload),
      })
      if (response.ok) {
        await fetchPosts()
        resetPostForm()
        setShowPostForm(false)
      } else {
        const error = await response.json()
        console.error('Create post error response:', error)
        alert(`Failed to create post: ${error.detail || "Unknown error"}`)
      }
    } catch (error) {
      console.error("Failed to create post:", error)
      alert("Failed to create post")
    } finally {
      setPostSubmitting(false)
    }
  }

  const handleUpdatePost = async () => {
    if (!editingPost) return
    try {
      const cleanedPayload = cleanPostPayload(postForm)
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/posts/${editingPost.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify(cleanedPayload),
      })
      if (response.ok) {
        await fetchPosts()
        setEditingPost(null)
        resetPostForm()
      } else {
        const error = await response.json()
        alert(`Failed to update post: ${error.detail || "Unknown error"}`)
      }
    } catch (error) {
      console.error("Failed to update post:", error)
      alert("Failed to update post")
    }
  }

  const handleDeletePost = async (postId: string) => {
    if (!confirm("Are you sure you want to delete this post?")) return
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/posts/${postId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      })
      if (response.ok) {
        await fetchPosts()
      } else {
        alert("Failed to delete post")
      }
    } catch (error) {
      console.error("Failed to delete post:", error)
      alert("Failed to delete post")
    }
  }

  const handleUploadFeaturedImage = async (postId: string, file: File) => {
    const formData = new FormData()
    formData.append("file", file)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/posts/${postId}/featured-image`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: formData,
      })
      if (response.ok) {
        const data = await response.json()
        setPostForm({ ...postForm, featured_image_url: data.featured_image_url })
        await fetchPosts()
      } else {
        alert("Failed to upload image")
      }
    } catch (error) {
      console.error("Failed to upload image:", error)
      alert("Failed to upload image")
    }
  }

  const resetPostForm = () => {
    setPostForm({
      title: "",
      slug: "",
      markdown_content: "",
      html_content: "",
      excerpt: "",
      post_type: "news",
      status: "draft",
      featured_image_url: "",
      category_ids: [],
      tag_ids: [],
    })
  }

  const startEditPost = (post: BlogPost) => {
    setEditingPost(post)
    setPostForm({
      title: post.title,
      slug: post.slug,
      markdown_content: post.markdown_content || "",
      html_content: post.html_content || "",
      excerpt: post.excerpt || "",
      post_type: post.post_type,
      status: post.status,
      featured_image_url: post.featured_image_url || "",
      category_ids: post.categories.map((c) => c.id),
      tag_ids: post.tags.map((t) => t.id),
    })
    setShowPostForm(true)
  }

  const handleCreateCategory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/categories`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify(categoryForm),
      })
      if (response.ok) {
        await fetchCategories()
        setCategoryForm({ name: "", slug: "", description: "" })
        setEditingCategory(null)
      } else {
        const error = await response.json()
        alert(`Failed to create category: ${error.detail || "Unknown error"}`)
      }
    } catch (error) {
      console.error("Failed to create category:", error)
      alert("Failed to create category")
    }
  }

  const handleUpdateCategory = async () => {
    if (!editingCategory) return
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/categories/${editingCategory.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify(categoryForm),
      })
      if (response.ok) {
        await fetchCategories()
        setEditingCategory(null)
        setCategoryForm({ name: "", slug: "", description: "" })
      } else {
        const error = await response.json()
        alert(`Failed to update category: ${error.detail || "Unknown error"}`)
      }
    } catch (error) {
      console.error("Failed to update category:", error)
      alert("Failed to update category")
    }
  }

  const handleDeleteCategory = async (categoryId: string) => {
    if (!confirm("Are you sure you want to delete this category?")) return
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/categories/${categoryId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      })
      if (response.ok) {
        await fetchCategories()
      } else {
        alert("Failed to delete category")
      }
    } catch (error) {
      console.error("Failed to delete category:", error)
      alert("Failed to delete category")
    }
  }

  const handleCreateTag = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/tags`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify(tagForm),
      })
      if (response.ok) {
        await fetchTags()
        setTagForm({ name: "", slug: "" })
        setEditingTag(null)
      } else {
        const error = await response.json()
        alert(`Failed to create tag: ${error.detail || "Unknown error"}`)
      }
    } catch (error) {
      console.error("Failed to create tag:", error)
      alert("Failed to create tag")
    }
  }

  const handleUpdateTag = async () => {
    if (!editingTag) return
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/tags/${editingTag.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify(tagForm),
      })
      if (response.ok) {
        await fetchTags()
        setEditingTag(null)
        setTagForm({ name: "", slug: "" })
      } else {
        const error = await response.json()
        alert(`Failed to update tag: ${error.detail || "Unknown error"}`)
      }
    } catch (error) {
      console.error("Failed to update tag:", error)
      alert("Failed to update tag")
    }
  }

  const handleDeleteTag = async (tagId: string) => {
    if (!confirm("Are you sure you want to delete this tag?")) return
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/blog/tags/${tagId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      })
      if (response.ok) {
        await fetchTags()
      } else {
        alert("Failed to delete tag")
      }
    } catch (error) {
      console.error("Failed to delete tag:", error)
      alert("Failed to delete tag")
    }
  }

  if (loading || !isAuthenticated || !isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex">
      <AdminSidebar />
      <div className="flex-1 ml-0 md:ml-[20px] p-4 md:p-6">
        <div className="absolute top-4 right-4 z-10">
          <ThemeToggle />
        </div>
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Blog Management</h1>
              <p className="text-muted-foreground">Manage blog posts, categories, and tags</p>
            </div>
            <Link href="/blog">
              <Button variant="outline">
                <Eye className="w-4 h-4 mr-2" />
                View Public Blog
              </Button>
            </Link>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 border-b">
            <button
              onClick={() => setActiveTab("posts")}
              className={`px-4 py-2 font-medium ${
                activeTab === "posts"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground"
              }`}
            >
              <FileText className="w-4 h-4 inline mr-2" />
              Posts
            </button>
            <button
              onClick={() => setActiveTab("categories")}
              className={`px-4 py-2 font-medium ${
                activeTab === "categories"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground"
              }`}
            >
              <Folder className="w-4 h-4 inline mr-2" />
              Categories
            </button>
            <button
              onClick={() => setActiveTab("tags")}
              className={`px-4 py-2 font-medium ${
                activeTab === "tags"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground"
              }`}
            >
              <Tag className="w-4 h-4 inline mr-2" />
              Tags
            </button>
          </div>

          {/* Posts Tab */}
          {activeTab === "posts" && (
            <div className="space-y-4">
              {!showPostForm ? (
                <>
                  <div className="flex justify-end">
                    <Button onClick={() => setShowPostForm(true)}>
                      <Plus className="w-4 h-4 mr-2" />
                      New Post
                    </Button>
                  </div>
                  <Card>
                    <CardContent className="p-0">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Title</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Author</TableHead>
                            <TableHead>Published</TableHead>
                            <TableHead>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {posts.map((post) => (
                            <TableRow key={post.id}>
                              <TableCell className="font-medium">{post.title}</TableCell>
                              <TableCell>
                                <Badge variant="outline">{post.post_type}</Badge>
                              </TableCell>
                              <TableCell>
                                <Badge
                                  variant={post.status === "published" ? "default" : "secondary"}
                                >
                                  {post.status}
                                </Badge>
                              </TableCell>
                              <TableCell>{post.author.name || post.author.email}</TableCell>
                              <TableCell>
                                {post.published_at
                                  ? new Date(post.published_at).toLocaleDateString()
                                  : "-"}
                              </TableCell>
                              <TableCell>
                                <div className="flex gap-2">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => startEditPost(post)}
                                  >
                                    <Edit className="w-4 h-4" />
                                  </Button>
                                  <Link href={`/blog/${post.slug}`} target="_blank">
                                    <Button variant="ghost" size="sm">
                                      <Eye className="w-4 h-4" />
                                    </Button>
                                  </Link>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDeletePost(post.id)}
                                  >
                                    <Trash2 className="w-4 h-4 text-destructive" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>
                        {editingPost ? "Edit Post" : "Create New Post"}
                      </CardTitle>
                      <Button variant="ghost" onClick={() => {
                        setShowPostForm(false)
                        setEditingPost(null)
                        resetPostForm()
                      }}>
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium mb-2 block">Title</label>
                        <Input
                          value={postForm.title}
                          onChange={(e) => setPostForm({ ...postForm, title: e.target.value })}
                          placeholder="Post title"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-2 block">Slug</label>
                        <Input
                          value={postForm.slug}
                          onChange={(e) => setPostForm({ ...postForm, slug: e.target.value })}
                          placeholder="url-friendly-slug"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium mb-2 block">Post Type</label>
                        <select
                          value={postForm.post_type}
                          title="Post Type"
                          onChange={(e) => setPostForm({ ...postForm, post_type: e.target.value })}
                          className="w-full px-3 py-2 border rounded-md"
                        >
                          <option value="news">News</option>
                          <option value="announcement">Announcement</option>
                          <option value="update">Update</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-2 block">Status</label>
                        <select
                          value={postForm.status}
                          title="Status"
                          onChange={(e) => setPostForm({ ...postForm, status: e.target.value })}
                          className="w-full px-3 py-2 border rounded-md"
                        >
                          <option value="draft">Draft</option>
                          <option value="published">Published</option>
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Excerpt</label>
                      <Textarea
                        value={postForm.excerpt}
                        onChange={(e) => setPostForm({ ...postForm, excerpt: e.target.value })}
                        placeholder="Short excerpt..."
                        rows={2}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Featured Image URL</label>
                      <div className="flex gap-2">
                        <Input
                          value={postForm.featured_image_url}
                          onChange={(e) =>
                            setPostForm({ ...postForm, featured_image_url: e.target.value })
                          }
                          placeholder="Image URL or upload file"
                        />
                        {editingPost && (
                          <input
                            type="file"
                            title="Upload Featured Image"
                            accept="image/*"
                            onChange={(e) => {
                              const file = e.target.files?.[0]
                              if (file && editingPost) {
                                handleUploadFeaturedImage(editingPost.id, file)
                              }
                            }}
                            className="hidden"
                            id="image-upload"
                          />
                        )}
                        {editingPost && (
                          <Button
                            variant="outline"
                            onClick={() => document.getElementById("image-upload")?.click()}
                          >
                            <Upload className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                    <BlogEditor
                      markdownContent={postForm.markdown_content}
                      htmlContent={postForm.html_content}
                      onMarkdownChange={(value) =>
                        setPostForm({ ...postForm, markdown_content: value })
                      }
                      onHtmlChange={(value) =>
                        setPostForm({ ...postForm, html_content: value })
                      }
                    />
                    <div>
                      <label className="text-sm font-medium mb-2 block">Categories</label>
                      <div className="flex flex-wrap gap-2">
                        {categories.map((category) => (
                          <Badge
                            key={category.id}
                            variant={
                              postForm.category_ids.includes(category.id) ? "default" : "outline"
                            }
                            className="cursor-pointer"
                            onClick={() => {
                              const newIds = postForm.category_ids.includes(category.id)
                                ? postForm.category_ids.filter((id) => id !== category.id)
                                : [...postForm.category_ids, category.id]
                              setPostForm({ ...postForm, category_ids: newIds })
                            }}
                          >
                            {category.name}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Tags</label>
                      <div className="flex flex-wrap gap-2">
                        {tags.map((tag) => (
                          <Badge
                            key={tag.id}
                            variant={postForm.tag_ids.includes(tag.id) ? "default" : "outline"}
                            className="cursor-pointer"
                            onClick={() => {
                              const newIds = postForm.tag_ids.includes(tag.id)
                                ? postForm.tag_ids.filter((id) => id !== tag.id)
                                : [...postForm.tag_ids, tag.id]
                              setPostForm({ ...postForm, tag_ids: newIds })
                            }}
                          >
                            {tag.name}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="outline"
                        onClick={() => {
                          setShowPostForm(false)
                          setEditingPost(null)
                          resetPostForm()
                        }}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={editingPost ? handleUpdatePost : handleCreatePost}
                        disabled={postSubmitting}
                      >
                        {postSubmitting ? (
                          <span className="flex items-center">
                            <svg className="animate-spin h-4 w-4 mr-2 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8z"></path>
                            </svg>
                            {editingPost ? "Updating..." : "Creating..."}
                          </span>
                        ) : (
                          <>
                            <Save className="w-4 h-4 mr-2" />
                            {editingPost ? "Update" : "Create"} Post
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Categories Tab */}
          {activeTab === "categories" && (
            <div className="space-y-4">
              <div className="flex justify-end">
                <Button
                  onClick={() => {
                    setEditingCategory(null)
                    setCategoryForm({ name: "", slug: "", description: "" })
                  }}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Category
                </Button>
              </div>
              {(editingCategory || (!editingCategory && categoryForm.name)) && (
                <Card>
                  <CardHeader>
                    <CardTitle>
                      {editingCategory ? "Edit Category" : "Create Category"}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Name</label>
                      <Input
                        value={categoryForm.name}
                        onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                        placeholder="Category name"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Slug</label>
                      <Input
                        value={categoryForm.slug}
                        onChange={(e) => setCategoryForm({ ...categoryForm, slug: e.target.value })}
                        placeholder="category-slug"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Description</label>
                      <Textarea
                        value={categoryForm.description}
                        onChange={(e) =>
                          setCategoryForm({ ...categoryForm, description: e.target.value })
                        }
                        placeholder="Category description"
                        rows={3}
                      />
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="outline"
                        onClick={() => {
                          setEditingCategory(null)
                          setCategoryForm({ name: "", slug: "", description: "" })
                        }}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={editingCategory ? handleUpdateCategory : handleCreateCategory}
                      >
                        <Save className="w-4 h-4 mr-2" />
                        {editingCategory ? "Update" : "Create"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
              <Card>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Slug</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {categories.map((category) => (
                        <TableRow key={category.id}>
                          <TableCell className="font-medium">{category.name}</TableCell>
                          <TableCell>{category.slug}</TableCell>
                          <TableCell>{category.description || "-"}</TableCell>
                          <TableCell>
                            <div className="flex gap-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setEditingCategory(category)
                                  setCategoryForm({
                                    name: category.name,
                                    slug: category.slug,
                                    description: category.description || "",
                                  })
                                }}
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteCategory(category.id)}
                              >
                                <Trash2 className="w-4 h-4 text-destructive" />
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
          )}

          {/* Tags Tab */}
          {activeTab === "tags" && (
            <div className="space-y-4">
              <div className="flex justify-end">
                <Button
                  onClick={() => {
                    setEditingTag(null)
                    setTagForm({ name: "", slug: "" })
                  }}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Tag
                </Button>
              </div>
              {(editingTag || (!editingTag && tagForm.name)) && (
                <Card>
                  <CardHeader>
                    <CardTitle>{editingTag ? "Edit Tag" : "Create Tag"}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Name</label>
                      <Input
                        value={tagForm.name}
                        onChange={(e) => setTagForm({ ...tagForm, name: e.target.value })}
                        placeholder="Tag name"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Slug</label>
                      <Input
                        value={tagForm.slug}
                        onChange={(e) => setTagForm({ ...tagForm, slug: e.target.value })}
                        placeholder="tag-slug"
                      />
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="outline"
                        onClick={() => {
                          setEditingTag(null)
                          setTagForm({ name: "", slug: "" })
                        }}
                      >
                        Cancel
                      </Button>
                      <Button onClick={editingTag ? handleUpdateTag : handleCreateTag}>
                        <Save className="w-4 h-4 mr-2" />
                        {editingTag ? "Update" : "Create"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
              <Card>
                <CardContent className="p-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Slug</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {tags.map((tag) => (
                        <TableRow key={tag.id}>
                          <TableCell className="font-medium">{tag.name}</TableCell>
                          <TableCell>{tag.slug}</TableCell>
                          <TableCell>
                            <div className="flex gap-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setEditingTag(tag)
                                  setTagForm({ name: tag.name, slug: tag.slug })
                                }}
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteTag(tag.id)}
                              >
                                <Trash2 className="w-4 h-4 text-destructive" />
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
          )}
        </div>
      </div>
    </div>
  )
}

