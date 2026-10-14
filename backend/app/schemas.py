from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Optional


class ToolSchema(BaseModel):
    name: str
    description: Optional[str] = None
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: Optional[dict[str, Any]] = None


class ServiceManifest(BaseModel):
    publisher: dict[str, Any]
    service: dict[str, Any]
    pricing: dict[str, Any]
    max_spend_per_call: Optional[float] = None
    refund_policy: str = "30d"


class ServiceCreate(BaseModel):
    publisher_id: str
    name: str
    description: str
    version: str = "1.0.0"
    mcp_endpoint: str
    tool_schemas: list[ToolSchema] = Field(default_factory=list)
    price_atomic: int
    currency: str = "USDC"
    chain: str = "base"
    manifest: dict[str, Any] = Field(default_factory=dict)


class ServiceOut(BaseModel):
    id: str
    publisher_id: str
    name: str
    description: str
    version: str
    mcp_endpoint: str
    tool_schemas: list[ToolSchema]
    price_atomic: int
    currency: str
    chain: str
    active: bool
    score: Optional[float] = None

    model_config = {"from_attributes": True}


class PublisherCreate(BaseModel):
    domain: str
    wallet_address: str
    display_name: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 20
    min_similarity: float = 0.25


class CallRequest(BaseModel):
    service_id: str
    agent_id: str = "anonymous"
    request_payload: dict[str, Any] = Field(default_factory=dict)
    payment_tx: Optional[str] = None  # x402 tx hash / signed payload reference
    receipt_number: Optional[str] = None  # credits receipt (web UI flow)
    success: bool = True  # client-reported execution result for receipt finalization
