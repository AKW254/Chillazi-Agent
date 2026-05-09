# =========================
# Build Stage
# =========================
FROM node:22-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .
# Inside your frontend/Dockerfile
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
# Build app
RUN npm run build

# =========================
# Production Stage
# =========================
FROM nginx:stable-alpine

# Copy build output
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose nginx port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]