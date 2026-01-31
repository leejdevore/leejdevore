/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    NEXT_PUBLIC_TILES_URL: process.env.NEXT_PUBLIC_TILES_URL || "http://localhost:3001",
  },
};

module.exports = nextConfig;
