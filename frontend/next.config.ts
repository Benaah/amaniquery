import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'res.cloudinary.com',
        pathname: '/**',
      },
    ],
  },
  // Configure path aliases for Turbopack
  experimental: {
    // @ts-expect-error - turbo.resolveAlias is available but types may not be updated
    turbo: {
      resolveAlias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
  },
  // Fallback webpack config for non-Turbopack builds
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, 'src'),
    };
    return config;
  },
};

export default nextConfig;
