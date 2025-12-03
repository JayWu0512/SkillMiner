# frontend/Dockerfile

# Use a lightweight Node.js image
FROM node:20-alpine

# Set working directory inside the container
WORKDIR /app

# Copy package manifests first (better Docker layer caching)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend source code
COPY . .

# Expose the dev server port (adjust if you use a different port)
EXPOSE 3000

# Start the dev server
# For Vite:  npm run dev -- --host 0.0.0.0 --port 3000
# For CRA:   npm start
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
