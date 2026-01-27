FROM node:18-alpine as build

WORKDIR /app

# Install dependencies first (cached layer)
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy config files
COPY tsconfig.json ./
COPY tailwind.config.js ./
COPY postcss.config.js ./

# Copy application code (changes frequently)
COPY public ./public
COPY src ./src

# Build production bundle
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

# Simple nginx config for SPA
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
