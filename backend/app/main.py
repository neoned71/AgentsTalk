from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
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
    if settings.environment == "production" and (not settings.jwt_secret or len(settings.jwt_secret) < 32):
        raise RuntimeError("JWT_SECRET must be set and at least 32 chars in production")
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is required (leave blank is invalid even in dev)")
    task = asyncio.create_task(_release_loop())
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE services ADD COLUMN IF NOT EXISTS search_tsv TSVECTOR"))
        # Ensure full-text search trigger exists when bootstrapping from SQLAlchemy metadata
        await conn.execute(text("""
        CREATE OR REPLACE FUNCTION services_tsv_update() RETURNS trigger AS $$
        BEGIN
          NEW.search_tsv :=
            setweight(to_tsvector('simple', coalesce(NEW.name, '')), 'A') ||
            setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'B') ||
            setweight(to_tsvector('simple', coalesce(array_to_string(ARRAY (SELECT jsonb_array_elements_text(NEW.tool_schemas)), ' '), '')), 'C');
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """))
        await conn.execute(text("""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'services_tsv_trigger') THEN
            CREATE TRIGGER services_tsv_trigger BEFORE INSERT OR UPDATE ON services
            FOR EACH ROW EXECUTE FUNCTION services_tsv_update();
          END IF;
        END $$;
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS services_tsv_idx ON services USING gin (search_tsv)"))
    yield
    task.cancel()
    await engine.dispose()


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AgentTalk", version="0.1.0", docs_url="/docs" if settings.environment != "production" else None, redoc_url=None, lifespan=lifespan)

from fastapi import Request
import logging

log = logging.getLogger("agenttalk")

@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    log.exception("unhandled error: %s", type(exc).__name__)
    return JSONResponse(status_code=500, content={"detail": "internal server error"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "environment": settings.environment}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unhealthy"})
