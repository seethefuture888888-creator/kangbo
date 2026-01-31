# 构建前端
FROM node:20-alpine AS builder
WORKDIR /app
COPY app/package.json app/package-lock.json* ./app/
WORKDIR /app/app
RUN npm ci
COPY app/ ./
RUN npm run build

# 用 nginx 提供静态文件
FROM nginx:alpine
COPY --from=builder /app/app/dist /usr/share/nginx/html
RUN echo 'server { root /usr/share/nginx/html; index index.html; location / { try_files $uri $uri/ /index.html; } location /data/ { alias /usr/share/nginx/html/data/; } }' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
