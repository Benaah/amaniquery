import { NextRequest, NextResponse } from "next/server"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function POST(request: NextRequest) {
  try {
    const sessionToken = request.headers.get("x-session-token")
    
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    }
    
    if (sessionToken) {
      headers["X-Session-Token"] = sessionToken
    }

    const response = await fetch(`${API_BASE_URL}/admin/retrain`, {
      method: "POST",
      headers,
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: "Failed to initiate retraining" },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error initiating retrain:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
