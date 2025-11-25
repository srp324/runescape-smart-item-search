# RuneScape Smart Item Search - Mobile App (iOS & Android)

React Native mobile application for searching OSRS items using semantic search. Supports both iOS and Android platforms.

## Prerequisites

- Node.js (>= 18)
- npm or yarn
- React Native development environment set up:
  - For iOS: Xcode and CocoaPods
  - For Android: Android Studio and Android SDK

## Installation

1. Install dependencies:
```bash
npm install
# or
yarn install
```

2. For iOS, install CocoaPods:
```bash
cd ios
pod install
cd ..
```

## Configuration

Update the API base URL in `apiClient.ts` if needed:

```typescript
const API_BASE_URL = __DEV__
  ? 'http://localhost:8000'  // Development - use your machine's IP for physical devices
  : 'https://your-production-api.com';  // Production URL
```

**Note:** For physical devices, replace `localhost` with your computer's IP address (e.g., `http://192.168.1.100:8000`).

## Running the App

### iOS
```bash
npm run ios
# or
yarn ios
```

### Android
```bash
npm run android
# or
yarn android
```

## Development

Start the Metro bundler:
```bash
npm start
# or
yarn start
```

## Project Structure

- `apiClient.ts` - API client for communicating with the FastAPI backend
- `SearchScreen.example.tsx` - Example search screen component

## API Endpoints

The app communicates with the FastAPI backend at `http://localhost:8000` (development):

- `POST /api/items/search` - Search items using semantic search
- `GET /api/items/{item_id}` - Get item details
- `GET /api/items/{item_id}/prices` - Get price history
- `GET /api/items/{item_id}/price/current` - Get current price

## Troubleshooting

### Network Issues on Physical Devices

If you're testing on a physical device, make sure:
1. Your device and computer are on the same network
2. The API base URL uses your computer's IP address, not `localhost`
3. Your firewall allows connections on port 8000

### Metro Bundler Issues

If you encounter Metro bundler issues:
```bash
npm start -- --reset-cache
```

