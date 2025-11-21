# Vercel Deployment Guide

This document describes the frontend deployment configuration for AmaniQuery on Vercel.

## Deployment URL

The frontend is deployed at: **https://amaniquery.vercel.app**

## Configuration

### Vercel Configuration File

The `frontend/vercel.json` file contains the Vercel-specific configuration:
- Framework: Next.js
- Build command: `npm run build`
- Security headers configured

### Environment Variables

Set the following environment variable in Vercel:

- **NEXT_PUBLIC_API_URL**: `https://api-amaniquery.onrender.com`

This points the frontend to the backend API deployed on Render.

## Deployment Steps

1. **Connect Repository to Vercel**
   - Go to [Vercel Dashboard](https://vercel.com)
   - Import your GitHub repository
   - Select the `frontend` directory as the root directory

2. **Configure Environment Variables**
   - In Vercel project settings, add:
     - `NEXT_PUBLIC_API_URL` = `https://api-amaniquery.onrender.com`

3. **Deploy**
   - Vercel will automatically detect Next.js and deploy
   - The app will be available at `https://amaniquery.vercel.app`

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│   Vercel        │         │     Render       │
│                 │         │                  │
│  Frontend       │────────▶│  FastAPI Backend │
│  (Next.js)      │  HTTPS  │  (Python)       │
│                 │         │                  │
│ amaniquery.     │         │ api-amaniquery.  │
│ vercel.app      │         │ onrender.com     │
└─────────────────┘         └──────────────────┘
```

## CORS Configuration

The backend API is configured to accept requests from:
- `https://amaniquery.vercel.app`
- `https://www.amaniquery.vercel.app`
- `http://localhost:3000` (for local development)
- `http://localhost:3001` (for local development)

## Troubleshooting

### Build Failures
- Ensure all dependencies are in `package.json`
- Check build logs in Vercel dashboard
- Verify Node.js version compatibility

### API Connection Issues
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check CORS configuration on backend
- Ensure backend API is running and accessible

### Environment Variables
- All `NEXT_PUBLIC_*` variables must be set in Vercel
- Changes require a new deployment to take effect
- Use Vercel's environment variable UI for production values

