from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.db import engine, Base, SessionLocal
from app.routers import publishers, services, search, calls, payouts, auth, receipts, billing, keys, routing
from app.routers.payouts import release_due


async def _release_loop():
    while True:
        try:
            async with SessionLocal() as session:
                await release_due(session)
        except Exception:
            pass
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_release_loop())
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    task.cancel()
    await engine.dispose()


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AgentTalk", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(publishers.router)
app.include_router(services.router)
app.include_router(search.router)
app.include_router(calls.router)
app.include_router(payouts.router)
app.include_router(receipts.router)
app.include_router(billing.router)
app.include_router(keys.router)
app.include_router(routing.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
