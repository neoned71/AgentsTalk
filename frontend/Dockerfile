FROM node:20-alpine
WORKDIR /app
RUN apk add --no-cache python3 make g++
ARG PUBLIC_API_BASE=https://agentstalk.neoned71.com/api
ENV PUBLIC_API_BASE=$PUBLIC_API_BASE
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm","run","preview","--","--host","0.0.0.0","--port","5173"]
