# frontend/Dockerfile

# ── Stage 1: Build ───────────────────────────
# Node builds the production bundle (the dist/ folder)
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 2: Serve ───────────────────────────
# We throw away Node entirely. The final image is just Nginx + your built files.
# This makes the image tiny (~25MB vs ~400MB).
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]