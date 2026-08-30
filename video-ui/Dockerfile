# ================================
# Build Stage
# ================================
FROM node:22-alpine AS builder

WORKDIR /app

# Install Dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source
COPY . .

# Build the SvelteKit app
RUN npm run build

# ================================
# Runtime Stage
# ================================
FROM node:22-alpine AS runtime

WORKDIR /app

# Optional: upgrade Alpine packages
RUN apk upgrade --no-cache

# Copy only production dependencies
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Copy built output from builder
COPY --from=builder /app/build ./build

# Optional: Copy static assets if needed
COPY --from=builder /app/package.json ./

ENV NODE_ENV=production
ENV HOST=0.0.0.0
# PORT was 3000
ENV PORT=5173

EXPOSE 5173

CMD ["node", "build"]
