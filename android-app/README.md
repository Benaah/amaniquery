# AmaniQuery Mobile App

React Native Android application for AmaniQuery - Kenya's AI Legal Assistant.

## Features

- **Chat Interface**: Query the legal knowledge base with streaming responses
- **Voice Agent**: Real-time voice conversations with LiveKit integration
- **Notifications**: Subscribe to news updates via SMS/WhatsApp

## Prerequisites

- Node.js 18+
- React Native development environment
- Android Studio with Android SDK
- Java Development Kit (JDK) 11+

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API_BASE_URL
```

3. Run on Android:
```bash
npm run android
```

## Environment Variables

- `API_BASE_URL`: Backend API URL (default: http://localhost:8000)
- `LIVEKIT_URL`: LiveKit WebSocket URL (optional, for voice)
- `ENABLE_NOTIFICATIONS`: Enable/disable push notifications

## Build

To create a release build:
```bash
cd android
./gradlew assembleRelease
```

The APK will be generated at `android/app/build/outputs/apk/release/app-release.apk`

