import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  trailingSlash: false,
  images: {
    domains: ["images-na.ssl-images-amazon.com"],
  },
};

export default nextConfig;
