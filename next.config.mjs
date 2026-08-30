/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  images: {
    unoptimized: true,
  },
  output: process.env.NEXT_EXPORT === 'true' ? 'export' : undefined,
  transpilePackages: [
    'three',
    '@react-three/fiber',
    '@react-three/drei',
    'lucide-react',
    'framer-motion'
  ],
};

export default nextConfig;
