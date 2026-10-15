from __future__ import annotations

import datetime
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/simulator", tags=["simulator"])


def _request_data(request: Request) -> Dict[str, Any]:
    # Accept any small JSON body sent by an agent; ignore failures for GET/HEAD.
    data: Dict[str, Any] = {}
    async def read_json():
        try:
            body = await request.json()
            if isinstance(body, dict):
                data.update(body)
        except Exception:
            pass
    # Synchronously fan in not possible, so only use path/populated defaults here.
    return data


def _reply(payload: Dict[str, Any]) -> JSONResponse:
    payload.setdefault("status", "ok")
    payload.setdefault("simulated", True)
    payload.setdefault("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
    return JSONResponse(payload)


@router.api_route("/ride", methods=["GET", "POST", "HEAD"])
async def ride(request: Request) -> Any:
    if request.method == "HEAD":
        return JSONResponse({})
    return _reply({
        "service": "simulated-ride-booking",
        "ride_id": "ride_501",
        "pickup": "Market Square",
        "dropoff": "Union Station",
        "eta_minutes": 8,
        "distance_km": 4.2,
        "price_usdc_atomic": 0,
        "driver": "Demo Driver",
        "vehicle": "Toyota Prius Demo",
    })


@router.api_route("/movie", methods=["GET", "POST", "HEAD"])
async def movie(request: Request) -> Any:
    if request.method == "HEAD":
        return JSONResponse({})
    return _reply({
        "service": "simulated-movie-ticket-booking",
        "theater": "Demo Cineplex",
        "movie": "Agent Demo",
        "showtime": "7:30 PM",
        "seats": ["A12", "A13"],
        "confirmation": "MOVIE-DEMO-789",
        "ticket_count": 2,
    })


@router.api_route("/restaurant", methods=["GET", "POST", "HEAD"])
async def restaurant(request: Request) -> Any:
    if request.method == "HEAD":
        return JSONResponse({})
    return _reply({
        "service": "simulated-restaurant-table-booking",
        "restaurant": "Demo Kitchen",
        "table": "T-7",
        "guests": 4,
        "date": "2026-10-15",
        "time": "7:00 PM",
        "confirmation": "TABLE-DEMO-321",
    })


@router.api_route("/shopping", methods=["GET", "POST", "HEAD"])
async def shopping(request: Request) -> Any:
    if request.method == "HEAD":
        return JSONResponse({})
    return _reply({
        "service": "simulated-shopping-marketplace",
        "search": "wireless charger",
        "products": [
            {"id": "P1001", "name": "Demo USB-C Charger", "price_usdc_atomic": 1200000, "in_stock": True},
            {"id": "P1002", "name": "Demo Wireless Pad", "price_usdc_atomic": 2400000, "in_stock": True},
        ],
        "order_id": None,
        "cart_total_usdc_atomic": 0,
    })


@router.api_route("/cloud", methods=["GET", "POST", "HEAD"])
async def cloud(request: Request) -> Any:
    if request.method == "HEAD":
        return JSONResponse({})
    return _reply({
        "service": "simulated-cloud-operations",
        "instances": [
            {"id": "i-demo-01", "status": "running", "cpu_hours": 2.4},
            {"id": "i-demo-02", "status": "stopped", "cpu_hours": 0.0},
        ],
        "last_operation": "status",
        "usage_usdc_atomic": 0,
    })
