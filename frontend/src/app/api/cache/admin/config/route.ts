import { NextRequest, NextResponse } from "next/server"
import { getCached, setCached, deleteCacheKey, CACHE_KEYS, CACHE_TTL } from "@/lib/redis"

export async function GET(request: NextRequest) {
    try {
        const cacheKey = CACHE_KEYS.ADMIN_CONFIG

        // Try to get from cache first
        const cached = await getCached(cacheKey)
        if (cached) {
            return NextResponse.json(cached, {
                headers: { "X-Cache": "HIT" },
            })
        }

        // Fetch from backend
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const userToken = request.headers.get("X-Session-Token") || null
        const headers: Record<string, string> = {}
        if (userToken) {
            headers["X-Session-Token"] = userToken
        }

        const response = await fetch(`${apiBaseUrl}/api/admin/config`, { headers })

        if (!response.ok) {
            return NextResponse.json(
                { error: "Failed to fetch config" },
                { status: response.status }
            )
        }

        const config = await response.json()

        // Cache the result
        await setCached(cacheKey, config, CACHE_TTL.ADMIN_CONFIG)

        return NextResponse.json(config, {
            headers: { "X-Cache": "MISS" },
        })
    } catch (error: any) {
        console.error("Config cache error:", error)
        return NextResponse.json(
            { error: error.message || "Internal server error" },
            { status: 500 }
        )
    }
}

// DELETE: Invalidate config cache
export async function DELETE() {
    try {
        const cacheKey = CACHE_KEYS.ADMIN_CONFIG
        await deleteCacheKey(cacheKey)
        return NextResponse.json({ success: true })
    } catch (error: any) {
        console.error("Delete config cache error:", error)
        return NextResponse.json(
            { error: error.message || "Internal server error" },
            { status: 500 }
        )
    }
}
