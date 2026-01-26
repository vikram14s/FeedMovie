# Multi-stage build for FeedMovie
# Stage 1: Build frontend
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend with frontend assets
FROM python:3.12-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copy other necessary files
COPY data/ ./data/ 2>/dev/null || true

# Expose port (Railway sets PORT env var)
EXPOSE 5000

# Start command - install Playwright browsers at runtime then start app
CMD ["sh", "-c", "playwright install --with-deps chromium && cd backend && python app.py"]
