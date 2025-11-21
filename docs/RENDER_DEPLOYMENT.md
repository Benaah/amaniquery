# Render Deployment Guide

This document describes the backend API deployment configuration for AmaniQuery on Render.

## Service URL

The backend API is deployed at: **https://api-amaniquery.onrender.com**

## URL Assignment

Render automatically assigns URLs based on the service name in `render.yaml`:
- Service name: `api-amaniquery`
- Assigned URL: `https://api-amaniquery.onrender.com`

The URL format is: `https://{service-name}.onrender.com`

## Configuration

### Render Blueprint (`render.yaml`)

The blueprint defines a single web service:

```yaml
services:
  - name: api-amaniquery
    type: web
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python start_api.py
    plan: free
```

**Note:** The `start_api.py` script is used to start the API. It automatically:
- Uses Render's `PORT` environment variable (or falls back to `API_PORT` or 8000)
- Disables reload in production (via `API_RELOAD=false`)
- Provides proper logging and initialization
- Can optionally start the voice agent if configured (disabled by default in production)

### Environment Variables

The following environment variables are configured in the blueprint:

- `CORS_ORIGINS`: Allowed CORS origins (includes Vercel frontend URLs)
- `API_HOST`: `0.0.0.0` (required for Render)
- `API_RELOAD`: `false` (disables auto-reload in production)
- `ENABLE_VOICE_AGENT`: `false` (disables voice agent in production)
- `LLM_PROVIDER`: `moonshot`
- `DEFAULT_MODEL`: `moonshot-v1-8k`
- `EMBEDDING_MODEL`: `all-MiniLM-L6-v2`

**Note:** The `start_api.py` script automatically uses Render's `PORT` environment variable (which Render provides automatically). You don't need to set `API_PORT` explicitly.

## Deployment Steps

1. **Prepare Repository**
   - Ensure `render.yaml` is in the root directory
   - Ensure `requirements.txt` exists with all Python dependencies

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will detect `render.yaml` automatically

3. **Review Services**
   - Render will show the `api-amaniquery` service
   - Verify the service name is correct (this determines the URL)
   - Review environment variables

4. **Deploy**
   - Click "Apply" to deploy
   - Render will build and deploy the service
   - The service will be available at `https://api-amaniquery.onrender.com`

## Verifying URL Assignment

After deployment:

1. Check the Render dashboard - the service should show the URL
2. The URL will be: `https://api-amaniquery.onrender.com`
3. Test the API: `curl https://api-amaniquery.onrender.com/health`

## Custom Domain (Optional)

If you want to use a custom domain instead of `api-amaniquery.onrender.com`:

1. Go to your service settings in Render
2. Navigate to "Custom Domains"
3. Add your custom domain
4. Follow DNS configuration instructions

**Note:** The default `api-amaniquery.onrender.com` URL will continue to work even with a custom domain.

## Troubleshooting

### Service Name Issues
- Ensure the service name in `render.yaml` is exactly `api-amaniquery`
- Service names are case-sensitive
- Service names must be unique within your Render account

### URL Not Accessible
- Check service status in Render dashboard
- Verify the service is running (not sleeping)
- Check build logs for errors
- Verify the start command is correct

### CORS Issues
- Ensure `CORS_ORIGINS` includes your frontend URL
- Check that the frontend URL matches exactly (including https://)
- Verify CORS configuration in the API code

## Architecture

```
┌──────────────────┐
│     Render       │
│                  │
│  FastAPI Backend │
│                  │
│ api-amaniquery.  │
│ onrender.com     │
└──────────────────┘
         ▲
         │ HTTPS
         │
┌─────────────────┐
│   Vercel        │
│                 │
│  Frontend       │
│  (Next.js)      │
│                 │
│ amaniquery.     │
│ vercel.app      │
└─────────────────┘
```

