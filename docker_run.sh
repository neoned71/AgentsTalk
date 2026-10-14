#!/bin/bash
set -e
cd "$(dirname "$0")"

# --- DB ---
docker container stop agenttalk_db 2>/dev/null || true
docker container remove agenttalk_db 2>/dev/null || true
docker volume create agenttalk_pgdata >/dev/null 2>&1 || true
docker run -d --restart unless-stopped --network "nginx_network" \
  --name agenttalk_db \
  -e POSTGRES_USER=agentshub \
  -e POSTGRES_PASSWORD=agentshub \
  -e POSTGRES_DB=agentshub \
  -v agenttalk_pgdata:/var/lib/postgresql/data \
  -v "$(pwd)/backend/sql/init.sql:/docker-entrypoint-initdb.d/init.sql:ro" \
  pgvector/pgvector:pg16 >/dev/null
echo "Waiting for DB..."
for i in $(seq 1 30); do
  if docker exec agenttalk_db pg_isready -U agentshub -d agentshub >/dev/null 2>&1; then break; fi
  sleep 1
done

# --- BACKEND ---
docker container stop agenttalk_backend 2>/dev/null || true
docker container remove agenttalk_backend 2>/dev/null || true
docker image remove neoned71_agenttalk_backend:1 2>/dev/null || true
docker build -f backend/Dockerfile -t neoned71_agenttalk_backend:1 backend/
docker run -d --restart unless-stopped --network "nginx_network" \
  --env-file deploy/home-server/.env \
  -e DATABASE_URL=postgresql+asyncpg://agentshub:agentshub@agenttalk_db:5432/agentshub \
  -e ENVIRONMENT=production \
  -e SECURE_COOKIES=true \
  -e CORS_ORIGINS=https://agentstalk.neoned71.com,https://agenttalk.neoned71.com \
  -e ALLOW_DEMO_TOPUP=false \
  --name agenttalk_backend \
  neoned71_agenttalk_backend:1

# --- FRONTEND ---
docker container stop agenttalk_frontend 2>/dev/null || true
docker container remove agenttalk_frontend 2>/dev/null || true
docker image remove neoned71_agenttalk_frontend:1 2>/dev/null || true
docker build -f frontend/Dockerfile -t neoned71_agenttalk_frontend:1 frontend/
docker run -d --restart unless-stopped --network "nginx_network" \
  -e PUBLIC_API_BASE=https://agentstalk.neoned71.com/api \
  --name agenttalk_frontend \
  neoned71_agenttalk_frontend:1

echo "AgentsTalk containers started:" && docker ps --format '{{.Names}} {{.Status}} {{.Ports}}' | grep agenttalk
