FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Vite mặc định chạy cổng 5173
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]