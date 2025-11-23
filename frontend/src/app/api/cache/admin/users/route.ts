import { NextRequest, NextResponse } from "next/server"
import { getCached, setCached, CACHE_KEYS, CACHE_TTL } from "@/lib/redis"

export async function GET(request: NextRequest) {
    try {
        // Get page from query params
        const searchParams = request.nextUrl.searchParams
        const page = parseInt(searchParams.get("page") || "1")
        const pageSize = searchParams.get("page_size") || "20"

        const cacheKey = CACHE_KEYS.ADMIN_USERS(page)

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

        const response = await fetch(
            `${apiBaseUrl}/api/v1/auth/admin/users?page=${page}&page_size=${pageSize}`,
            { headers }
        )

        if (!response.ok) {
            return NextResponse.json(
                { error: "Failed to fetch users" },
                { status: response.status }
            )
        }

        const users = await response.json()

        // Cache the result
        await setCached(cacheKey, users, CACHE_TTL.ADMIN_USERS)

        return NextResponse.json(users, {
            headers: { "X-Cache": "MISS" },
        })
    } catch (error: any) {
        console.error("Users cache error:", error)
        return NextResponse.json(
            { error: error.message || "Internal server error" },
            { status: 500 }
        )
    }
}
