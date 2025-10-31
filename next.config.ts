import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      // Proxy API requests to avoid mixed content issues
      {
        source: '/api/ubuntu/:path*',
        destination: 'http://192.168.1.19:5000/api/:path*',
      },
      {
        source: '/api/windows/:path*',
        destination: 'http://192.168.1.116:5000/api/:path*',
      },
      {
        source: '/api/old-staging/:path*',
        destination: 'http://135.148.164.94:5000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
