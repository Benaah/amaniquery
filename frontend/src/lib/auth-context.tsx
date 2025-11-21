"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"
import { useRouter } from "next/navigation"

interface User {
  id: string
  email: string
  name: string | null
  status: string
  email_verified: boolean
  phone_verified?: boolean
  last_login: string | null
  profile_image_url?: string | null
  created_at?: string
  updated_at?: string
  roles?: string[]
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  register: (email: string, password: string, name: string, phone_number: string) => Promise<User>
  isAuthenticated: boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check for existing session on mount
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const sessionToken = localStorage.getItem("session_token")
      if (!sessionToken) {
        setLoading(false)
        return
      }

      const response = await fetch(`${API_URL}/api/v1/auth/me`, {
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": sessionToken,
        },
      })

      if (response.ok) {
        const userData = await response.json()
        // Ensure roles is an array - handle both direct roles and nested roles
        if (userData.roles) {
          if (!Array.isArray(userData.roles)) {
            userData.roles = []
          }
        } else {
          userData.roles = []
        }
        console.log("User data from /me:", userData) // Debug log
        setUser(userData)
      } else {
        // If 401, clear session
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem("session_token")
          setUser(null)
        }
      }
    } catch (error) {
      console.error("Auth check failed:", error)
      localStorage.removeItem("session_token")
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Login failed")
      }

      const data = await response.json()
      
      // Store session token
      if (data.session_token) {
        localStorage.setItem("session_token", data.session_token)
      }

      // Ensure roles is an array
      if (data.user.roles && !Array.isArray(data.user.roles)) {
        data.user.roles = []
      } else if (!data.user.roles) {
        data.user.roles = []
      }

      console.log("Login response user data:", data.user) // Debug log
      
      // Set user immediately with proper roles handling
      setUser(data.user)

      // Check for redirect query parameter first
      const urlParams = new URLSearchParams(window.location.search)
      const redirectTo = urlParams.get("redirect")
      
      // Redirect based on role or redirect parameter
      // Use data.user directly since state update is async
      const userRoles = data.user.roles || []
      const isAdmin = Array.isArray(userRoles) && userRoles.includes("admin")
      console.log("Is admin?", isAdmin, "Roles:", userRoles) // Debug log
      
      if (redirectTo) {
        router.push(redirectTo)
      } else if (isAdmin) {
        router.push("/admin")
      } else {
        router.push("/chat")
      }
    } catch (error) {
      console.error("Login error:", error)
      throw error
    }
  }

  const register = async (
    email: string,
    password: string,
    name: string,
    phone_number: string
  ): Promise<User> => {
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password, name, phone_number }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Registration failed")
      }

      const userData = await response.json()
      return userData
    } catch (error) {
      console.error("Registration error:", error)
      throw error
    }
  }

  const logout = async () => {
    try {
      const sessionToken = localStorage.getItem("session_token")
      if (sessionToken) {
        await fetch(`${API_URL}/api/v1/auth/logout`, {
          method: "POST",
          headers: {
            "X-Session-Token": sessionToken,
          },
        })
      }
    } catch (error) {
      console.error("Logout error:", error)
    } finally {
      localStorage.removeItem("session_token")
      setUser(null)
      router.push("/auth/signin")
    }
  }

  const isAuthenticated = !!user
  // Check if user has admin role - ensure roles is an array
  const userRoles = user?.roles || []
  const isAdmin = Array.isArray(userRoles) && userRoles.includes("admin")

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        register,
        isAuthenticated,
        isAdmin,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

