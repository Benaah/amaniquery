"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import {
  Home,
  MessageSquare,
  Mic,
  User,
  LogOut,
  Menu,
  X,
} from "lucide-react"
import { Button } from "./ui/button"
import { cn } from "@/lib/utils"

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const pathname = usePathname()
  const router = useRouter()
  const { user, logout } = useAuth()

  // Auto-hide on desktop, show on mobile toggle
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener("resize", checkMobile)
    return () => window.removeEventListener("resize", checkMobile)
  }, [])

  const handleLogout = async () => {
    await logout()
  }

  const navItems = [
    { href: "/", icon: Home, label: "Home" },
    { href: "/chat", icon: MessageSquare, label: "Chat" },
    { href: "/voice", icon: Mic, label: "Voice" },
    { href: "/profile", icon: User, label: "Profile" },
  ]

  // Desktop: Show on hover at left edge
  // Mobile: Toggle with hamburger button
  const shouldShow = isMobile ? isOpen : isHovered

  return (
    <>
      {/* Mobile Hamburger Button */}
      {isMobile && (
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="fixed top-4 left-4 z-50 p-2 rounded-lg bg-background border shadow-lg md:hidden"
          aria-label="Toggle menu"
        >
          {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      )}

      {/* Mobile Overlay */}
      {isMobile && isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 h-full bg-background border-r z-40 transition-all duration-300 ease-in-out",
          isMobile
            ? cn(
                "w-64",
                isOpen ? "translate-x-0" : "-translate-x-full"
              )
            : cn(
                "w-64",
                shouldShow ? "translate-x-0" : "-translate-x-[calc(100%-20px)]"
              )
        )}
        onMouseEnter={() => !isMobile && setIsHovered(true)}
        onMouseLeave={() => !isMobile && setIsHovered(false)}
      >
        <div className="flex flex-col h-full p-4">
          {/* Logo/Header */}
          <div className="mb-6">
            <h2 className="text-xl font-bold">AmaniQuery</h2>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => isMobile && setIsOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-accent"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>

          {/* User Profile Section */}
          <div className="border-t pt-4 mt-4">
            {user && (
              <div className="mb-4">
                <div className="flex items-center gap-3 px-4 py-2">
                  {user.profile_image_url ? (
                    <div className="relative w-10 h-10 rounded-full overflow-hidden flex-shrink-0">
                      <img
                        src={user.profile_image_url}
                        alt={user.name || "Profile"}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-primary" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{user.name || user.email}</p>
                    <p className="text-sm text-muted-foreground truncate">{user.email}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Logout Button */}
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={handleLogout}
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      {/* Spacer for desktop (to prevent content overlap) */}
      {!isMobile && (
        <div className="w-[20px] fixed left-0 top-0 h-full z-30 pointer-events-none" />
      )}
    </>
  )
}

