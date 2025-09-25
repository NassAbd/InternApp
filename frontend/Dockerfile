# Use a Node.js 20 base image (non-Alpine) to avoid native binary issues.
FROM node:20-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json to leverage Docker cache
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port Vite runs on
EXPOSE 5173

# Command to run the Vite dev server, accessible from the host
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]