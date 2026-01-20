# worker/Dockerfile
FROM node:20-slim

WORKDIR /app

# Install system dependencies including bash for scripts
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    jq \
    bc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
RUN curl -fsSL https://claude.ai/install.sh | bash || true

# Install Node.js dependencies
COPY package.json .
RUN npm install

# Copy TypeScript config and source
COPY tsconfig.json .
COPY src/ ./src/

# Build TypeScript
RUN npm run build

# Create data directory
RUN mkdir -p /data/projects

# Run the worker
CMD ["node", "dist/index.js"]
