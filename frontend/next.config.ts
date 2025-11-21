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
  // Configure path aliases for webpack
  webpack: (config) => {
    // Use process.cwd() which works reliably in Next.js builds
    const srcPath = path.join(process.cwd(), 'src');
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      '@': srcPath,
    };
    return config;
  },
};

export default nextConfig;
