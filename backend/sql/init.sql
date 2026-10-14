CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE publishers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain TEXT UNIQUE NOT NULL,
    wallet_address TEXT NOT NULL,
    display_name TEXT,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    publisher_id UUID NOT NULL REFERENCES publishers(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0.0',
    mcp_endpoint TEXT NOT NULL,
    manifest JSONB NOT NULL DEFAULT '{}',
    tool_schemas JSONB NOT NULL DEFAULT '[]',
    price_atomic BIGINT NOT NULL,            -- price per call in USDC smallest unit (6 decimals)
    currency TEXT NOT NULL DEFAULT 'USDC',
    chain TEXT NOT NULL DEFAULT 'base',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    last_latency_ms INTEGER,
    last_ping_at TIMESTAMPTZ,
    embedding VECTOR(768),
    search_tsv TSVECTOR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX services_embedding_idx ON services USING hnsw (embedding vector_cosine_ops);
CREATE INDEX services_tsv_idx ON services USING gin (search_tsv);
CREATE INDEX services_name_trgm_idx ON services USING gin (name gin_trgm_ops);
CREATE INDEX services_publisher_idx ON services (publisher_id);

CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID NOT NULL REFERENCES services(id),
    agent_id TEXT NOT NULL,
    request_hash TEXT,
    result_hash TEXT,
    price_atomic BIGINT NOT NULL,
    tx_hash TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | settled | refunded | released
    escrow_release_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX calls_service_idx ON calls (service_id);
CREATE INDEX calls_status_idx ON calls (status);

CREATE TABLE payouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    publisher_id UUID NOT NULL REFERENCES publishers(id),
    amount_atomic BIGINT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USDC',
    tx_hash TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- trigger to keep search_tsv updated
CREATE OR REPLACE FUNCTION services_tsv_update() RETURNS trigger AS $$
BEGIN
  NEW.search_tsv :=
    setweight(to_tsvector('simple', coalesce(NEW.name, '')), 'A') ||
    setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'B') ||
    setweight(to_tsvector('simple', coalesce(array_to_string(ARRAY(SELECT jsonb_array_elements_text(NEW.tool_schemas)), ' '), '')), 'C');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER services_tsv_trigger BEFORE INSERT OR UPDATE ON services
FOR EACH ROW EXECUTE FUNCTION services_tsv_update();
