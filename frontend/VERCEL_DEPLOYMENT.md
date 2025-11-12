# Vercel Deployment Guide for AmaniQuery Frontend

## Prerequisites

1. A Vercel account
2. Your GitHub repository connected to Vercel
3. Your backend API deployed and accessible

## Deployment Steps

### 1. Connect Repository to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository (`amaniquery`)
4. Configure the project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (should be automatic)
   - **Output Directory**: `.next` (should be automatic)

### 2. Set Environment Variables

In the Vercel dashboard, go to your project settings and add the following environment variable:

- **Name**: `NEXT_PUBLIC_API_URL`
- **Value**: Your production API URL (e.g., `https://your-api-domain.com`)
- **Environment**: Production

### 3. Deploy

1. Click "Deploy"
2. Wait for the build to complete
3. Your app will be available at `amaniquery.vercel.app`

## Custom Domain (Optional)

If you want to use a custom domain instead of the default Vercel domain:

1. Go to your project settings in Vercel
2. Navigate to "Domains"
3. Add your custom domain
4. Follow Vercel's DNS configuration instructions

## Troubleshooting

- **Build fails**: Check that all dependencies are properly listed in `package.json`
- **API calls fail**: Verify the `NEXT_PUBLIC_API_URL` environment variable is set correctly
- **404 errors**: Ensure your Next.js routing is configured properly

## Environment Variables Reference

- `NEXT_PUBLIC_API_URL`: URL of your backend API (required for production)
