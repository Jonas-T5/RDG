# frontend/Dockerfile
FROM node:20-slim AS builder

WORKDIR /app

# Install dependencies
COPY package.json .
RUN npm install

# Copy source files
COPY . .

# Build the application
RUN npm run build

# Production image
FROM node:20-slim AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy built application
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
