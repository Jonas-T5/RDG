/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: 'http://api:8000/:path*',
            },
            {
                source: '/ws/:path*',
                destination: 'http://api:8000/ws/:path*',
            },
        ];
    },
};

module.exports = nextConfig;
