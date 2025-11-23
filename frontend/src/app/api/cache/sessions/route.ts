import { NextRequest, NextResponse } from "next/server"
import { getCached, setCached, CACHE_KEYS, CACHE_TTL, getUserTokenHash } from "@/lib/redis"

export async function GET(request: NextRequest) {
    try {
        const userToken = request.headers.get("X-Session-Token") || null
        const tokenHash = getUserTokenHash(userToken)
        const cacheKey = CACHE_KEYS.SESSIONS(tokenHash)

        // Try to get from cache first
        const cached = await getCached(cacheKey)
        if (cached) {
            return NextResponse.json(cached, {
                headers: { "X-Cache": "HIT" },
            })
        }

        // Fetch from backend
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const headers: Record<string, string> = {
            "Content-Type": "application/json",
        }
        if (userToken) {
            headers["X-Session-Token"] = userToken
        }

        const response = await fetch(`${apiBaseUrl}/chat/sessions`, {
            headers,
        })

        if (!response.ok) {
            return NextResponse.json(
                { error: "Failed to fetch sessions" },
                { status: response.status }
            )
        }

        const sessions = await response.json()

        // Cache the result
        await setCached(cacheKey, sessions, CACHE_TTL.SESSIONS)

        return NextResponse.json(sessions, {
            headers: { "X-Cache": "MISS" },
        })
    } catch (error: any) {
        console.error("Sessions cache error:", error)
        return NextResponse.json(
            { error: error.message || "Internal server error" },
            { status: 500 }
        )
    }
}

// DELETE: Invalidate sessions cache
export async function DELETE(request: NextRequest) {
    try {
        const userToken = request.headers.get("X-Session-Token") || null
        const tokenHash = getUserTokenHash(userToken)
        const cacheKey = CACHE_KEYS.SESSIONS(tokenHash)

        const { deleteCacheKey } = await import("@/lib/redis")
        await deleteCacheKey(cacheKey)

        return NextResponse.json({ success: true })
    } catch (error: any) {
        console.error("Delete sessions cache error:", error)
        return NextResponse.json(
            { error: error.message || "Internal server error" },
            { status: 500 }
        )
    }
}
