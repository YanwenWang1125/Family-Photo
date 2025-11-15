/** @type {import('next').NextConfig} */
const nextConfig = {
  // TODO: Configure image domains for Azure Blob Storage
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '*.blob.core.windows.net',
      },
    ],
  },
  // TODO: Add other configuration as needed
}

module.exports = nextConfig
