import { fileURLToPath } from 'node:url';
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: fileURLToPath(new URL('.', import.meta.url)),
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${(process.env.BACKEND_URL || 'http://127.0.0.1:4000').replace(/\/$/, '')}/api/:path*`,
      },
    ];
  },
  async redirects() {
    return [
      {
        source: '/demo-video',
        destination: 'https://youtube.com', // Change this URL later
        permanent: false,
      },
    ];
  },
};
export default nextConfig;
