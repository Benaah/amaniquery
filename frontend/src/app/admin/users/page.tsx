"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { AdminSidebar } from "@/components/admin-sidebar"
import { ThemeToggle } from "@/components/theme-toggle"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"
import {
  Users,
  Search,
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Loader2,
  MoreVertical,
  Edit,
  Trash2,
  Ban,
  CheckCheck,
  ShieldOff,
  ShieldCheck,
  Activity,
  Filter,
} from "lucide-react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface User {
  id: string
  email: string
  name: string | null
  status: string
  email_verified: boolean
  last_login: string | null
  created_at: string
  updated_at: string
  roles?: string[]
}

interface AdminStats {
  total_users: number
  active_users: number
  suspended_users: number
  verified_users: number
  unverified_users: number
}

export default function AdminUsersPage() {
  const { isAuthenticated, isAdmin, loading } = useAuth()
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [loadingUsers, setLoadingUsers] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [verificationFilter, setVerificationFilter] = useState<string>("all")
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  
  // Dialog states
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [editFormData, setEditFormData] = useState({ name: "", email: "", status: "" })
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/signin?redirect=/admin/users")
    } else if (!loading && isAuthenticated && !isAdmin) {
      router.push("/chat")
    }
  }, [isAuthenticated, isAdmin, loading, router])

  useEffect(() => {
    if (isAuthenticated && isAdmin) {
      fetchUsers()
      fetchStats()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter, verificationFilter, isAuthenticated, isAdmin])

  const fetchStats = async () => {
    try {
      const sessionToken = localStorage.getItem("session_token")
      const response = await fetch(`${API_URL}/api/v1/auth/admin/stats`, {
        headers: {
          "X-Session-Token": sessionToken || "",
        },
      })
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch {
      // Stats are optional, don't show error
    }
  }

  const fetchUsers = async () => {
    setLoadingUsers(true)
    try {
      const sessionToken = localStorage.getItem("session_token")
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      })
      
      if (searchQuery) params.append("search", searchQuery)
      if (statusFilter !== "all") params.append("status", statusFilter)
      if (verificationFilter !== "all") params.append("email_verified", verificationFilter)
      
      const response = await fetch(
        `${API_URL}/api/v1/auth/admin/users?${params}`,
        {
          headers: {
            "X-Session-Token": sessionToken || "",
          },
        }
      )

      if (response.ok) {
        const data = await response.json()
        setUsers(data.users || [])
        setTotal(data.total || 0)
      } else {
        toast.error("Failed to fetch users")
      }
    } catch {
      toast.error("Failed to fetch users")
    } finally {
      setLoadingUsers(false)
    }
  }

  const handleEditUser = (user: User) => {
    setSelectedUser(user)
    setEditFormData({
      name: user.name || "",
      email: user.email,
      status: user.status,
    })
    setEditDialogOpen(true)
  }

  const handleSaveEdit = async () => {
    if (!selectedUser) return
    
    setActionLoading(true)
    try {
      const sessionToken = localStorage.getItem("session_token")
      const response = await fetch(
        `${API_URL}/api/v1/auth/admin/users/${selectedUser.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "X-Session-Token": sessionToken || "",
          },
          body: JSON.stringify({
            name: editFormData.name || null,
            email: editFormData.email,
            status: editFormData.status,
          }),
        }
      )

      if (response.ok) {
        toast.success("User updated successfully")
        setEditDialogOpen(false)
        fetchUsers()
        fetchStats()
      } else {
        const error = await response.json()
        toast.error(error.detail || "Failed to update user")
      }
    } catch {
      toast.error("Failed to update user")
    } finally {
      setActionLoading(false)
    }
  }

  const handleVerifyEmail = async (userId: string, verify: boolean) => {
    try {
      const sessionToken = localStorage.getItem("session_token")
      const endpoint = verify ? "verify-email" : "unverify-email"
      const response = await fetch(
        `${API_URL}/api/v1/auth/admin/users/${userId}/${endpoint}`,
        {
          method: "POST",
          headers: {
            "X-Session-Token": sessionToken || "",
          },
        }
      )

      if (response.ok) {
        toast.success(verify ? "Email verified" : "Email unverified")
        fetchUsers()
        fetchStats()
      } else {
        toast.error("Failed to update verification status")
      }
    } catch {
      toast.error("Failed to update verification status")
    }
  }

  const handleSuspendUser = async (userId: string, suspend: boolean) => {
    try {
      const sessionToken = localStorage.getItem("session_token")
      const endpoint = suspend ? "suspend" : "activate"
      const response = await fetch(
        `${API_URL}/api/v1/auth/admin/users/${userId}/${endpoint}`,
        {
          method: "POST",
          headers: {
            "X-Session-Token": sessionToken || "",
          },
        }
      )

      if (response.ok) {
        toast.success(suspend ? "User suspended" : "User activated")
        fetchUsers()
        fetchStats()
      } else {
        toast.error("Failed to update user status")
      }
    } catch {
      toast.error("Failed to update user status")
    }
  }

  const handleDeleteUser = async () => {
    if (!selectedUser) return
    
    setActionLoading(true)
    try {
      const sessionToken = localStorage.getItem("session_token")
      const response = await fetch(
        `${API_URL}/api/v1/auth/admin/users/${selectedUser.id}`,
        {
          method: "DELETE",
          headers: {
            "X-Session-Token": sessionToken || "",
          },
        }
      )

      if (response.ok) {
        toast.success("User deleted successfully")
        setDeleteDialogOpen(false)
        fetchUsers()
        fetchStats()
      } else {
        const error = await response.json()
        toast.error(error.detail || "Failed to delete user")
      }
    } catch {
      toast.error("Failed to delete user")
    } finally {
      setActionLoading(false)
    }
  }

  const handleRevokeSession = async (userId: string) => {
    try {
      const sessionToken = localStorage.getItem("session_token")
      const response = await fetch(
        `${API_URL}/api/v1/auth/admin/users/${userId}/revoke-sessions`,
        {
          method: "POST",
          headers: {
            "X-Session-Token": sessionToken || "",
          },
        }
      )

      if (response.ok) {
        const data = await response.json()
        toast.success(`Revoked ${data.sessions_revoked} session(s)`)
      } else {
        toast.error("Failed to revoke sessions")
      }
    } catch {
      toast.error("Failed to revoke sessions")
    }
  }


  const filteredUsers = users.filter(
    (user) =>
      user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (user.name && user.name.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const totalPages = Math.ceil(total / pageSize)

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
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Users className="w-8 h-8" />
              User Management
            </h1>
            <p className="text-muted-foreground">Manage all users in the system</p>
          </div>

          {/* Search and Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Filter className="w-5 h-5" />
                Filters & Search
              </CardTitle>
              <CardDescription>
                {stats && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Total Users</p>
                      <p className="text-2xl font-bold">{stats.total_users}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Active</p>
                      <p className="text-2xl font-bold text-green-600">{stats.active_users}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Suspended</p>
                      <p className="text-2xl font-bold text-red-600">{stats.suspended_users}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Verified</p>
                      <p className="text-2xl font-bold text-blue-600">{stats.verified_users}</p>
                    </div>
                  </div>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="relative md:col-span-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <Input
                    placeholder="Search users..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && fetchUsers()}
                    className="pl-10"
                  />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                    <SelectItem value="suspended">Suspended</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={verificationFilter} onValueChange={setVerificationFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Filter by verification" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Users</SelectItem>
                    <SelectItem value="true">Verified Only</SelectItem>
                    <SelectItem value="false">Unverified Only</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Users Table */}
          <Card>
            <CardHeader>
              <CardTitle>All Users</CardTitle>
            </CardHeader>
            <CardContent>
              {loadingUsers ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Email</TableHead>
                          <TableHead>Name</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Verified</TableHead>
                          <TableHead>Roles</TableHead>
                          <TableHead>Last Login</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredUsers.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                              No users found
                            </TableCell>
                          </TableRow>
                        ) : (
                          filteredUsers.map((user) => (
                            <TableRow key={user.id}>
                              <TableCell className="font-medium">{user.email}</TableCell>
                              <TableCell>{user.name || "—"}</TableCell>
                              <TableCell>
                                <Badge
                                  variant={
                                    user.status === "active" ? "default" :
                                    user.status === "suspended" ? "destructive" : 
                                    "secondary"
                                  }
                                >
                                  {user.status}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                {user.email_verified ? (
                                  <CheckCircle className="w-5 h-5 text-green-600" />
                                ) : (
                                  <XCircle className="w-5 h-5 text-yellow-600" />
                                )}
                              </TableCell>
                              <TableCell>
                                {user.roles && user.roles.length > 0 ? (
                                  <div className="flex gap-1 flex-wrap">
                                    {user.roles.map((role) => (
                                      <Badge key={role} variant="outline" className="text-xs">
                                        {role}
                                      </Badge>
                                    ))}
                                  </div>
                                ) : (
                                  <span className="text-muted-foreground text-sm">—</span>
                                )}
                              </TableCell>
                              <TableCell className="text-sm text-muted-foreground">
                                {user.last_login
                                  ? new Date(user.last_login).toLocaleDateString()
                                  : "Never"}
                              </TableCell>
                              <TableCell className="text-right">
                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="sm">
                                      <MoreVertical className="w-4 h-4" />
                                    </Button>
                                  </DropdownMenuTrigger>
                                  <DropdownMenuContent align="end" className="w-56">
                                    <DropdownMenuLabel>User Actions</DropdownMenuLabel>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem onClick={() => handleEditUser(user)}>
                                      <Edit className="w-4 h-4 mr-2" />
                                      Edit User
                                    </DropdownMenuItem>
                                    <DropdownMenuItem onClick={() => handleVerifyEmail(user.id, !user.email_verified)}>
                                      {user.email_verified ? (
                                        <>
                                          <ShieldOff className="w-4 h-4 mr-2" />
                                          Unverify Email
                                        </>
                                      ) : (
                                        <>
                                          <ShieldCheck className="w-4 h-4 mr-2" />
                                          Verify Email
                                        </>
                                      )}
                                    </DropdownMenuItem>
                                    <DropdownMenuItem onClick={() => handleSuspendUser(user.id, user.status !== "suspended")}>
                                      {user.status === "suspended" ? (
                                        <>
                                          <CheckCheck className="w-4 h-4 mr-2" />
                                          Activate Account
                                        </>
                                      ) : (
                                        <>
                                          <Ban className="w-4 h-4 mr-2" />
                                          Suspend Account
                                        </>
                                      )}
                                    </DropdownMenuItem>
                                    <DropdownMenuItem onClick={() => handleRevokeSession(user.id)}>
                                      <Activity className="w-4 h-4 mr-2" />
                                      Revoke Sessions
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem
                                      onClick={() => {
                                        setSelectedUser(user)
                                        setDeleteDialogOpen(true)
                                      }}
                                      className="text-red-600"
                                    >
                                      <Trash2 className="w-4 h-4 mr-2" />
                                      Delete User
                                    </DropdownMenuItem>
                                  </DropdownMenuContent>
                                </DropdownMenu>
                              </TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-between mt-4">
                      <div className="text-sm text-muted-foreground">
                        Page {page} of {totalPages}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setPage((p) => Math.max(1, p - 1))}
                          disabled={page === 1}
                        >
                          <ChevronLeft className="w-4 h-4" />
                          Previous
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                          disabled={page === totalPages}
                        >
                          Next
                          <ChevronRight className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Edit User Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
            <DialogDescription>
              Update user information and account settings.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Name</Label>
              <Input
                id="edit-name"
                value={editFormData.name}
                onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                placeholder="User name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-email">Email</Label>
              <Input
                id="edit-email"
                type="email"
                value={editFormData.email}
                onChange={(e) => setEditFormData({ ...editFormData, email: e.target.value })}
                placeholder="user@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-status">Status</Label>
              <Select
                value={editFormData.status}
                onValueChange={(value: string) => setEditFormData({ ...editFormData, status: value })}
              >
                <SelectTrigger id="edit-status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                  <SelectItem value="suspended">Suspended</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)} disabled={actionLoading}>
              Cancel
            </Button>
            <Button onClick={handleSaveEdit} disabled={actionLoading}>
              {actionLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete User Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete User</DialogTitle>
            <DialogDescription>
              Are you sure you want to permanently delete this user? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {selectedUser && (
            <div className="py-4">
              <div className="p-4 bg-muted rounded-lg space-y-2">
                <p className="text-sm">
                  <span className="font-medium">Email:</span> {selectedUser.email}
                </p>
                <p className="text-sm">
                  <span className="font-medium">Name:</span> {selectedUser.name || "—"}
                </p>
                <p className="text-sm">
                  <span className="font-medium">Status:</span> {selectedUser.status}
                </p>
              </div>
              <p className="text-sm text-red-600 mt-4">
                ⚠️ All user data, sessions, and associated records will be permanently deleted.
              </p>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)} disabled={actionLoading}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteUser} disabled={actionLoading}>
              {actionLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete User
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

