# Use Node Alpine for minimal base image
FROM node:20-alpine

WORKDIR /app

# Copy package files for better layer caching
COPY package*.json ./

# Use npm ci for clean, reproducible installs
RUN npm ci

# Copy application code
COPY . .

EXPOSE 5173

# Run the development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]