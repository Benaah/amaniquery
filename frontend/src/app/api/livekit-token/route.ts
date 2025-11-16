import { NextRequest, NextResponse } from "next/server"
import { AccessToken } from "livekit-server-sdk"

export async function POST(request: NextRequest) {
  try {
    const { roomName, participantName } = await request.json()

    if (!roomName) {
      return NextResponse.json(
        { error: "roomName is required" },
        { status: 400 }
      )
    }

    // Use server-side environment variables only (not NEXT_PUBLIC_* which are exposed to client)
    // These must match the credentials used by your LiveKit server
    const apiKey = process.env.LIVEKIT_API_KEY
    const apiSecret = process.env.LIVEKIT_API_SECRET

    if (!apiKey) {
      return NextResponse.json(
        { 
          error: "LIVEKIT_API_KEY not configured",
          hint: "Set LIVEKIT_API_KEY environment variable (server-side, not NEXT_PUBLIC_*). This must match the API key configured in your LiveKit server. Get it from LiveKit Cloud dashboard (Settings > Keys) or your self-hosted LiveKit config."
        },
        { status: 500 }
      )
    }

    if (!apiSecret) {
      return NextResponse.json(
        { 
          error: "LIVEKIT_API_SECRET not configured",
          hint: "Set LIVEKIT_API_SECRET environment variable (server-side). This must match the API secret configured in your LiveKit server.",
          instructions: [
            "For LiveKit Cloud:",
            "  1. Go to Settings > Keys in your LiveKit Cloud dashboard",
            "  2. Click on your API key row or the menu (three dots) to reveal the secret",
            "  3. If the secret is not visible, you may need to create a NEW API key",
            "  4. When creating a new key, copy BOTH the API key AND the secret immediately",
            "  5. Note: Secrets are only shown once when created - save it securely!",
            "",
            "For self-hosted LiveKit:",
            "  - Check your LiveKit server configuration file (usually livekit.yaml)",
            "  - Or use the default 'secret' for development mode"
          ]
        },
        { status: 500 }
      )
    }

    // Validate API secret format - it should NOT be a JWT token
    const trimmedSecret = apiSecret.trim()
    if (trimmedSecret.startsWith('eyJ')) {
      console.error(`[LiveKit Token] ❌ ERROR: API secret appears to be a JWT token, not a secret key!`)
      console.error(`[LiveKit Token] The secret starts with 'eyJ' which indicates it's a JWT token.`)
      console.error(`[LiveKit Token] LiveKit API secret should be a random string, not a token.`)
      return NextResponse.json(
        { 
          error: "Invalid API secret format",
          hint: "Your LIVEKIT_API_SECRET appears to be a JWT token (starts with 'eyJ'), but it should be the actual secret key. In LiveKit Cloud: Go to Settings > Keys and copy the 'API Secret' (not a token). It should be a long random string, not a JWT token.",
          details: "The API secret is used to SIGN tokens, not a token itself. Make sure you're using the secret key from your LiveKit dashboard, not a generated token."
        },
        { status: 500 }
      )
    }

    // Log API key prefix for debugging (without exposing full key or secret)
    console.log(`[LiveKit Token] Using API key: ${apiKey.substring(0, 8)}...`)
    console.log(`[LiveKit Token] API secret length: ${trimmedSecret.length} characters`)
    console.log(`[LiveKit Token] API secret starts with: ${trimmedSecret.substring(0, 4)}...`)
    
    // Warn if secret looks suspicious
    if (trimmedSecret.length < 20) {
      console.warn(`[LiveKit Token] ⚠️  WARNING: API secret is very short (${trimmedSecret.length} chars). LiveKit secrets are usually much longer.`)
    }

    const at = new AccessToken(apiKey, trimmedSecret, {
      identity: participantName || "user",
    })

    at.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
    })

    const token = await at.toJwt()
    
    // Decode token to verify it was created correctly (for debugging)
    const tokenParts = token.split('.')
    if (tokenParts.length === 3) {
      try {
        const payload = JSON.parse(Buffer.from(tokenParts[1], 'base64').toString())
        console.log(`[LiveKit Token] Generated token details:`)
        console.log(`  - Room: ${payload.video?.room}`)
        console.log(`  - Identity: ${payload.sub}`)
        console.log(`  - Issuer (API Key): ${payload.iss}`)
        console.log(`  - Expires: ${new Date(payload.exp * 1000).toISOString()}`)
        console.log(`[LiveKit Token] ⚠️  If token validation fails, verify:`)
        console.log(`  1. API Key in token (${payload.iss}) matches your LiveKit server's API key`)
        console.log(`  2. API Secret used to sign token matches your LiveKit server's API secret`)
        console.log(`  3. Both are set in your Next.js environment variables (not NEXT_PUBLIC_*)`)
      } catch (e) {
        // Ignore decode errors
        console.error(`[LiveKit Token] Failed to decode token payload:`, e)
      }
    }

    return NextResponse.json({ token })
  } catch (error) {
    console.error("[LiveKit Token] Error generating token:", error)
    const errorMessage = error instanceof Error ? error.message : "Failed to generate token"
    
    // Provide detailed troubleshooting information
    const troubleshooting = {
      error: errorMessage,
      hint: "Token signature verification failed. This means the API secret doesn't match your LiveKit server.",
      steps: [
        "1. Verify LIVEKIT_API_KEY matches your LiveKit server's API key",
        "2. Verify LIVEKIT_API_SECRET matches your LiveKit server's API secret (exactly, including any spaces)",
        "3. For LiveKit Cloud: Get credentials from Settings > Keys in your dashboard",
        "4. For self-hosted: Check your LiveKit server configuration file",
        "5. Ensure environment variables are set in .env.local (not .env) for Next.js",
        "6. Restart your Next.js dev server after changing environment variables"
      ]
    }
    
    return NextResponse.json(troubleshooting, { status: 500 })
  }
}

