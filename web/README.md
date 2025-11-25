# RuneScape Smart Item Search - Web App (Desktop)

React web application for searching OSRS items using semantic search. Runs in any modern web browser on Windows, macOS, and Linux.

## Prerequisites

- Node.js (>= 18)
- npm or yarn

## Installation

1. Install dependencies:
```bash
npm install
# or
yarn install
```

## Configuration

The API base URL is configured in `src/apiClient.ts`. By default, it uses:
- Development: `http://localhost:8000`
- Production: Set via `VITE_API_URL` environment variable

To change the API URL, create a `.env` file:
```env
VITE_API_URL=http://your-api-url.com
```

## Running the App

### Development
```bash
npm run dev
# or
yarn dev
```

This will start the development server at `http://localhost:3000` and automatically open it in your browser.

### Production Build
```bash
npm run build
# or
yarn build
```

The built files will be in the `dist` directory.

### Preview Production Build
```bash
npm run preview
# or
yarn preview
```

## Features

- Semantic search for OSRS items
- Filter by members-only or free-to-play
- View item details including examine text, value, high alch, and GE limit
- Responsive design that works on desktop and tablet screens

## API Endpoints

The app communicates with the FastAPI backend:

- `POST /api/items/search` - Search items using semantic search
- `GET /api/items/{item_id}` - Get item details
- `GET /api/items/{item_id}/prices` - Get price history
- `GET /api/items/{item_id}/price/current` - Get current price

## Troubleshooting

### CORS Issues

If you encounter CORS errors, make sure the FastAPI backend has CORS enabled for your domain. The backend should already be configured to allow all origins in development.

### API Connection Issues

If the app can't connect to the API:
1. Make sure the FastAPI backend is running on `http://localhost:8000`
2. Check that the API URL in `apiClient.ts` matches your backend URL
3. For production, set the `VITE_API_URL` environment variable

