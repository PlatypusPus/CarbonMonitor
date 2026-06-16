# CarbonTrace frontend image — multi-stage: build with Node, serve with nginx.
# Stage 1 compiles the React app to static files; stage 2 serves them tiny+fast.

# --- Stage 1: build ---
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# --- Stage 2: serve ---
FROM nginx:1.27-alpine
# SPA fallback so client-side routes (e.g. /trends) don't 404 on refresh.
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
