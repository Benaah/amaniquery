# AmaniQuery Android App Setup Guide

## Prerequisites

1. **Node.js 18+** - Install from [nodejs.org](https://nodejs.org/)
2. **Java Development Kit (JDK) 11+** - Install from [adoptium.net](https://adoptium.net/)
3. **Android Studio** - Install from [developer.android.com](https://developer.android.com/studio)
4. **Android SDK** - Install via Android Studio SDK Manager
   - Android SDK Platform 34
   - Android SDK Build-Tools 34.0.0
   - Android Emulator (optional, for testing)

## Installation Steps

### 1. Install Dependencies

```bash
cd android-app
npm install
```

### 2. Configure Environment Variables

Create a `.env` file in the `android-app` directory:

```env
API_BASE_URL=http://10.0.2.2:8000
LIVEKIT_URL=wss://your-livekit-server.com
ENABLE_NOTIFICATIONS=true
```

**Note:** 
- For Android emulator, use `http://10.0.2.2:8000` instead of `localhost`
- For physical device, use your computer's IP address (e.g., `http://192.168.1.100:8000`)

### 3. Start Metro Bundler

```bash
npm start
```

### 4. Run on Android

In a new terminal:

```bash
npm run android
```

Or use Android Studio:
1. Open `android-app/android` in Android Studio
2. Wait for Gradle sync to complete
3. Click "Run" button or press Shift+F10

## Backend API Requirements

The app expects the following endpoints:

### Chat Endpoints
- `POST /chat/sessions` - Create chat session
- `GET /chat/sessions` - List sessions
- `GET /chat/sessions/{id}/messages` - Get messages
- `POST /chat/sessions/{id}/messages` - Send message (with streaming support)
- `POST /chat/feedback` - Submit feedback

### Voice Endpoints
- `POST /api/livekit-token` - Generate LiveKit token
  - Request body: `{ roomName, participantName, voice? }`
  - Response: `{ token: string }`

**Note:** You need to add the LiveKit token endpoint to your FastAPI backend. See `Module4_NiruAPI/api.py` for reference.

### Notifications Endpoints
- `GET /api/v1/notifications/sources` - Get notification sources
- `POST /api/v1/notifications/subscribe` - Create subscription
- `GET /api/v1/notifications/subscriptions` - List subscriptions
- `DELETE /api/v1/notifications/subscriptions/{id}` - Delete subscription

## Building for Release

### 1. Generate Signing Key (first time only)

```bash
cd android/app
keytool -genkeypair -v -storetype PKCS12 -keystore amaniquery-release.keystore -alias amaniquery-key -keyalg RSA -keysize 2048 -validity 10000
```

### 2. Configure Signing

Edit `android/app/build.gradle`:

```gradle
signingConfigs {
    release {
        storeFile file('amaniquery-release.keystore')
        storePassword 'your-password'
        keyAlias 'amaniquery-key'
        keyPassword 'your-password'
    }
}
buildTypes {
    release {
        signingConfig signingConfigs.release
        // ... rest of config
    }
}
```

### 3. Build APK

```bash
cd android
./gradlew assembleRelease
```

The APK will be at: `android/app/build/outputs/apk/release/app-release.apk`

## Troubleshooting

### Metro Bundler Issues
- Clear cache: `npm start -- --reset-cache`
- Delete `node_modules` and reinstall

### Android Build Issues
- Clean build: `cd android && ./gradlew clean`
- Invalidate caches in Android Studio: File > Invalidate Caches

### Network Issues
- Ensure backend API is running
- Check firewall settings
- For emulator, use `10.0.2.2` instead of `localhost`
- For device, ensure phone and computer are on same network

### LiveKit Issues
- Ensure LiveKit server is running
- Check `LIVEKIT_URL` in `.env`
- Verify token generation endpoint is implemented in backend

## Development Tips

1. **Hot Reload**: Shake device/emulator and select "Reload"
2. **Debugging**: Use React Native Debugger or Chrome DevTools
3. **Logs**: Use `react-native log-android` or Android Studio Logcat
4. **Testing**: Use Android Emulator or physical device with USB debugging enabled

