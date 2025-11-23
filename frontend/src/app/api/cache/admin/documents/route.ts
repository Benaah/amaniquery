import { NextRequest, NextResponse } from "next/server"
import { getCached, setCached, CACHE_KEYS, CACHE_TTL, hashQueryString } from "@/lib/redis"

export async function GET(request: NextRequest) {
    try {
        // Get query string and hash it for cache key
        const queryString = request.nextUrl.search || ""
        const queryHash = hashQueryString(queryString)
        const cacheKey = CACHE_KEYS.ADMIN_DOCUMENTS(queryHash)

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

        const response = await fetch(`${apiBaseUrl}/admin/documents${queryString}`, { headers })

        if (!response.ok) {
            return NextResponse.json(
                { error: "Failed to fetch documents" },
                { status: response.status }
            )
        }

        const documents = await response.json()

        // Cache the result
        await setCached(cacheKey, documents, CACHE_TTL.ADMIN_DOCUMENTS)

        return NextResponse.json(documents, {
            headers: { "X-Cache": "MISS" },
        })
    } catch (error: any) {
        console.error("Documents cache error:", error)
        return NextResponse.json(
            { error: error.message || "Internal server error" },
            { status: 500 }
        )
    }
}
