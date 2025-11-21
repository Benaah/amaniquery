# AmaniQuery Frontend

This is a [Next.js](https://nextjs.org) project for the AmaniQuery frontend application.

## Getting Started

First, install dependencies:

```bash
npm install
```

Then, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Environment Variables

Create a `.env.local` file in the root directory with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_AUTOCOMPLETE=true
```

### Available Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8000`)
- `NEXT_PUBLIC_ENABLE_AUTOCOMPLETE`: Enable/disable autocomplete feature (default: `true`)
  - Set to `"false"` to disable autocomplete suggestions
  - Set to `"true"` or omit to enable autocomplete

For production, set the `NEXT_PUBLIC_API_URL` environment variable to point to your deployed backend API.

## Deploy on Vercel

1. Connect your GitHub repository to Vercel
2. Set the following environment variable in Vercel:
   - `NEXT_PUBLIC_API_URL`: Your production API URL (e.g., `https://api-amaniquery.onrender.com`)
3. Deploy!

The app will be available at `https://amaniquery.vercel.app` once deployed.

**Note:** The frontend is deployed on Vercel, while the backend API is deployed on Render. Make sure to set the `NEXT_PUBLIC_API_URL` environment variable in Vercel to point to your Render API URL.

## Build Commands

- `npm run build` - Build the application
- `npm run start` - Start the production server
- `npm run lint` - Run ESLint
