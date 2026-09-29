# Stage 1: Build React App
FROM node:20-alpine AS build

WORKDIR /app

# Cache package manifests
COPY package.json package-lock.json* ./
RUN npm install

# Build static assets
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build output from Stage 1
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
