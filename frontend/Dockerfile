# Canopy Frontend Dockerfile
# Multi-stage build for development and production

# ============================================
# Stage 1: Base image with Node.js
# ============================================
FROM node:20-alpine as base

WORKDIR /app

# Copy package files
COPY package*.json ./

# ============================================
# Stage 2: Development image
# ============================================
FROM base as development

# Install all dependencies including devDependencies
RUN npm install

# Copy source code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run Vite dev server with HMR
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ============================================
# Stage 3: Build stage for production
# ============================================
FROM base as builder

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# ============================================
# Stage 4: Production image with Nginx
# ============================================
FROM nginx:alpine as production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
