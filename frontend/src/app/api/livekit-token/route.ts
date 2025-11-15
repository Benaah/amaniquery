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

    const apiKey = process.env.NEXT_PUBLIC_LIVEKIT_API_KEY || process.env.LIVEKIT_API_KEY

    if (!apiKey) {
      return NextResponse.json(
        { error: "LIVEKIT_API_KEY not configured" },
        { status: 500 }
      )
    }

    const at = new AccessToken(apiKey, undefined, {
      identity: participantName || "user",
    })

    at.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
    })

    const token = await at.toJwt()

    return NextResponse.json({ token })
  } catch (error) {
    console.error("Error generating token:", error)
    return NextResponse.json(
      { error: "Failed to generate token" },
      { status: 500 }
    )
  }
}

