import { NextRequest, NextResponse } from "next/server"
import { getCached, setCached, CACHE_KEYS, CACHE_TTL } from "@/lib/redis"

export async function GET(request: NextRequest) {
    try {
        const cacheKey = CACHE_KEYS.ADMIN_STATS

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

        const response = await fetch(`${apiBaseUrl}/stats`, { headers })

        if (!response.ok) {
            return NextResponse.json(
                { error: "Failed to fetch stats" },
                { status: response.status }
            )
        }

        const stats = await response.json()

        // Cache the result
        await setCached(cacheKey, stats, CACHE_TTL.ADMIN_STATS)

        return NextResponse.json(stats, {
            headers: { "X-Cache": "MISS" },
        })
    } catch (error: any) {
        console.error("Stats cache error:", error)
        return NextResponse.json(
            { error: error.message || "Internal server error" },
            { status: 500 }
        )
    }
}
