# Build stage
FROM node:20-alpine AS builder

# Use alpine-based image and install only necessary dependencies
RUN apk add --no-cache openssl

WORKDIR /app

# Copy only necessary files for dependency installation
COPY package.json yarn.lock ./

RUN yarn install --frozen-lockfile \
  && yarn cache clean

# Copy source files and build
COPY . .
RUN yarn run build

# Production stage
FROM node:20-alpine

LABEL maintainer="FAIR Data Innovations Hub <contact@fairdataihub.org>" \
  description="Alt text generation service frontend."

# Install openssl for Node.js runtime
RUN apk add --no-cache openssl

WORKDIR /app

# Copy only the necessary files from builder stage
COPY --from=builder /app/.output ./

# Copy our startup script and make it executable
COPY scripts/start.sh /app/scripts/start.sh
RUN chmod +x /app/scripts/start.sh

EXPOSE 3000

# Run startup script
CMD ["/app/scripts/start.sh"]