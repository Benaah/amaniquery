import { NextRequest, NextResponse } from "next/server"
import { getCached, setCached, deleteCacheKey, CACHE_KEYS, CACHE_TTL } from "@/lib/redis"

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ sessionId: string }> }
) {
    try {
        const { sessionId } = await params
        const cacheKey = CACHE_KEYS.SESSION_MESSAGES(sessionId)

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
        const headers: Record<string, string> = {
            "Content-Type": "application/json",
        }
        if (userToken) {
            headers["X-Session-Token"] = userToken
        }

        const response = await fetch(
            `${apiBaseUrl}/api/v1/chat/sessions/${sessionId}/messages`,
            { headers }
        )

        if (!response.ok) {
            return NextResponse.json(
                { error: "Failed to fetch messages" },
                { status: response.status }
            )
        }

        const messages = await response.json()

        // Cache the result
        await setCached(cacheKey, messages, CACHE_TTL.SESSION_MESSAGES)

        return NextResponse.json(messages, {
            headers: { "X-Cache": "MISS" },
        })
    } catch (error: unknown) {
        console.error("Messages cache error:", error)
        const errorMessage = typeof error === "object" && error !== null && "message" in error ? (error as { message?: string }).message : "Internal server error";
        return NextResponse.json(
            { error: errorMessage || "Internal server error" },
            { status: 500 }
        )
    }
}

// DELETE: Invalidate messages cache for a specific session
export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ sessionId: string }> }
) {
    try {
        const { sessionId } = await params
        const cacheKey = CACHE_KEYS.SESSION_MESSAGES(sessionId)
        await deleteCacheKey(cacheKey)

        return NextResponse.json({ success: true })
    } catch (error: unknown) {
        console.error("Delete messages cache error:", error)
        const errorMessage = typeof error === "object" && error !== null && "message" in error ? (error as { message?: string }).message : "Internal server error";
        return NextResponse.json(
            { error: errorMessage || "Internal server error" },
            { status: 500 }
        )
    }
}
