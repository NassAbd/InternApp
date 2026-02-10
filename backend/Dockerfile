# Multi-stage build: Base stage with Playwright dependencies
FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy AS playwright-base

WORKDIR /app

# Install Playwright package and only Chromium browser (skip Firefox and WebKit)
RUN pip install playwright && playwright install chromium

# Final stage: Use slim Python image
FROM python:3.11-slim-bullseye

WORKDIR /app

# Install only the minimal system dependencies needed for Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copy Chromium browser from playwright-base stage
COPY --from=playwright-base /ms-playwright /ms-playwright

# Set environment variables for Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]