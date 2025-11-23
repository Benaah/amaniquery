import { Redis } from "@upstash/redis"

// Initialize Redis client with Upstash credentials
const redis = new Redis({
    url: process.env.UPSTASH_REDIS_REST_URL!,
    token: process.env.UPSTASH_REDIS_REST_TOKEN!,
})

// Cache key prefixes
export const CACHE_KEYS = {
    SESSIONS: (userToken: string) => `sessions:user:${hashToken(userToken)}`,
    SESSION_MESSAGES: (sessionId: string) => `session:${sessionId}:messages`,
    // Admin cache keys
    ADMIN_STATS: "admin:stats",
    ADMIN_HEALTH: "admin:health",
    ADMIN_DATABASES: "admin:databases",
    ADMIN_DATABASE_STORAGE: "admin:database-storage",
    ADMIN_DOCUMENTS: (queryHash: string) => `admin:documents:${queryHash}`,
    ADMIN_CONFIG: "admin:config",
    ADMIN_ANALYTICS: "admin:analytics",
    ADMIN_USERS: (page: number) => `admin:users:${page}`,
}

// Default TTL values (in seconds)
export const CACHE_TTL = {
    SESSIONS: 300, // 5 minutes
    SESSION_MESSAGES: 600, // 10 minutes
    // Admin TTLs (shorter for frequently changing data)
    ADMIN_STATS: 60, // 1 minute
    ADMIN_HEALTH: 60, // 1 minute
    ADMIN_DATABASES: 120, // 2 minutes
    ADMIN_DATABASE_STORAGE: 120, // 2 minutes
    ADMIN_DOCUMENTS: 120, // 2 minutes
    ADMIN_CONFIG: 300, // 5 minutes
    ADMIN_ANALYTICS: 120, // 2 minutes
    ADMIN_USERS: 120, // 2 minutes
}

// Simple hash function for user tokens
function hashToken(token: string): string {
    // Use a simple hash to avoid storing sensitive tokens in Redis keys
    let hash = 0
    for (let i = 0; i < token.length; i++) {
        const char = token.charCodeAt(i)
        hash = (hash << 5) - hash + char
        hash = hash & hash // Convert to 32bit integer
    }
    return Math.abs(hash).toString(36)
}

/**
 * Get cached data from Redis
 */
export async function getCached<T>(key: string): Promise<T | null> {
    try {
        const data = await redis.get<T>(key)
        return data
    } catch (error) {
        console.error("Redis get error:", error)
        return null
    }
}

/**
 * Set cached data in Redis with optional TTL
 */
export async function setCached(
    key: string,
    value: any,
    ttl: number = 600
): Promise<void> {
    try {
        await redis.setex(key, ttl, JSON.stringify(value))
    } catch (error) {
        console.error("Redis set error:", error)
    }
}

/**
 * Delete a specific cache key
 */
export async function deleteCacheKey(key: string): Promise<void> {
    try {
        await redis.del(key)
    } catch (error) {
        console.error("Redis delete error:", error)
    }
}

/**
 * Invalidate cache keys matching a pattern
 */
export async function invalidateCache(pattern: string): Promise<void> {
    try {
        // Upstash Redis supports SCAN command
        let cursor: number | string = 0
        do {
            const result = await redis.scan(cursor, {
                match: pattern,
                count: 100,
            })
            cursor = result[0]
            const keys = result[1]

            if (keys.length > 0) {
                await redis.del(...keys)
            }
        } while (cursor !== 0 && cursor !== "0")
    } catch (error) {
        console.error("Redis invalidate error:", error)
    }
}

/**
 * Get user token hash for cache keys
 */
export function getUserTokenHash(token: string | null): string {
    return token ? hashToken(token) : "anonymous"
}

/**
 * Generate a simple hash for query strings
 */
export function hashQueryString(query: string): string {
    return hashToken(query)
}
