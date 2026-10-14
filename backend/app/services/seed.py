from __future__ import annotations

import uuid
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password
from app.models import Publisher, Service, User
from app.config import settings
from app.services.embeddings import get_embedder


CURATED_DOMAIN = "agentscurated.local"
CURATED_WALLET = "0x060c4366C213b9412e8a491a9809f988FF51FE28"


CURATED_SERVICES: List[Dict[str, Any]] = [
    {
        "name": "GitHub MCP Gateway",
        "description": "GitHub repository and issue tools: search code, read files, list pull requests, and inspect repository metadata.",
        "mcp_endpoint": "https://mcp_curated.agentshub.local/github",
        "price_atomic": 3000,
        "tool_schemas": [
            {"name": "search_repositories", "description": "Search GitHub repositories by query."},
            {"name": "get_file_contents", "description": "Read a file from a repository."},
            {"name": "list_pull_requests", "description": "List pull requests for a repository."},
        ],
    },
    {
        "name": "Slack MCP Bridge",
        "description": "Slack communication tools: list channels, read messages, and post updates.",
        "mcp_endpoint": "https://mcp_curated.agentshub.local/slack",
        "price_atomic": 2500,
        "tool_schemas": [
            {"name": "list_channels", "description": "List accessible Slack channels."},
            {"name": "read_messages", "description": "Read recent channel messages."},
            {"name": "post_message", "description": "Post a message to a channel."},
        ],
    },
    {
        "name": "Filesystem MCP",
        "description": "Local file system tools for reading, writing, and searching files in an allowed directory.",
        "mcp_endpoint": "https://mcp_curated.agentshub.local/filesystem",
        "price_atomic": 1200,
        "tool_schemas": [
            {"name": "read_file", "description": "Read file contents."},
            {"name": "write_file", "description": "Create or replace a file."},
            {"name": "search_files", "description": "Search files by pattern."},
        ],
    },
    {
        "name": "PostgreSQL MCP",
        "description": "PostgreSQL exploration tools: inspect schemas, run read-only SQL queries, and summarize database structure.",
        "mcp_endpoint": "https://mcp_curated.agentshub.local/postgres",
        "price_atomic": 4000,
        "tool_schemas": [
            {"name": "list_tables", "description": "List database tables."},
            {"name": "describe_table", "description": "Describe columns and constraints."},
            {"name": "run_read_query", "description": "Run a read-only SQL query."},
        ],
    },
    {
        "name": "Brave Search MCP",
        "description": "Web search tools for current information lookup and result summarization.",
        "mcp_endpoint": "https://mcp_curated.agentshub.local/brave-search",
        "price_atomic": 1500,
        "tool_schemas": [
            {"name": "web_search", "description": "Search the web for current information."},
            {"name": "summarize_results", "description": "Summarize top search results."},
        ],
    },
    {
        "name": "Memory MCP Graph",
        "description": "Persistent memory tools for storing observations and recalling related entities across agent sessions.",
        "mcp_endpoint": "https://mcp_curated.agentshub.local/memory",
        "price_atomic": 1800,
        "tool_schemas": [
            {"name": "create_entities", "description": "Create memory entities."},
            {"name": "add_observations", "description": "Add observations to entities."},
            {"name": "search_nodes", "description": "Search saved memory nodes."},
        ],
    },
    {
        "name": "Fetch MCP",
        "description": "HTTP fetching tools for downloading web pages, APIs, and structured documents.",
        "mcp_endpoint": "https://mcp_curated.agentshub.local/fetch",
        "price_atomic": 1000,
        "tool_schemas": [
            {"name": "fetch_url", "description": "Fetch a URL and return its content."},
            {"name": "parse_json", "description": "Parse JSON from a fetched response."},
        ],
    },
]


async def seed_curated_services(session: AsyncSession) -> None:
    pub_res = await session.execute(select(Publisher).where(Publisher.domain == CURATED_DOMAIN))
    publisher = pub_res.scalar_one_or_none()
    if publisher is None:
        publisher = Publisher(
            id=uuid.uuid4(),
            user_id=None,
            domain=CURATED_DOMAIN,
            wallet_address=CURATED_WALLET,
            display_name="AgentsTalk Curated",
            verified=True,
        )
        session.add(publisher)
        await session.flush()

    existing_names = set()
    svc_res = await session.execute(select(Service.name).where(Service.publisher_id == publisher.id))
    existing_names = {row[0] for row in svc_res.all()}

    embedder = None
    try:
        embedder = get_embedder()
    except Exception:
        embedder = None

    for item in CURATED_SERVICES:
        if item["name"] in existing_names:
            continue
        text_for_embed = item["name"] + "\n" + item["description"] + "\n" + "\n".join(
            f"{tool.get('name','')}: {tool.get('description','')}" for tool in item.get("tool_schemas", [])
        )
        embedding = None
        if embedder is not None:
            try:
                embedding = await embedder.embed(text_for_embed)
            except Exception:
                embedding = None

        service = Service(
            publisher_id=publisher.id,
            name=item["name"],
            description=item["description"],
            version=item.get("version", "1.0.0"),
            mcp_endpoint=item["mcp_endpoint"],
            tool_schemas=item.get("tool_schemas", []),
            price_atomic=int(item["price_atomic"]),
            currency=item.get("currency", "USDC"),
            chain=item.get("chain", "base"),
            manifest=item.get("manifest", {}),
            embedding=embedding,
            active=True,
        )
        session.add(service)


async def seed_admin_user(session):
    if not settings.admin_email or not settings.admin_password:
        return
    result = await session.execute(select(User).where(User.email == settings.admin_email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            display_name="Platform Admin",
            role="admin",
        )
        session.add(user)
    else:
        user.role = "admin"
        user.password_hash = hash_password(settings.admin_password)
