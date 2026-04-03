from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class OrderItem(BaseModel):
    name: str
    quantity: int
    is_core_item: bool = False
    is_heavy: bool = False  # e.g. cases of water, bulk items


class OrderTimestamps(BaseModel):
    received: Optional[str] = None
    picking_started: Optional[str] = None
    picked: Optional[str] = None
    dispatched: Optional[str] = None
    delivered: Optional[str] = None


class Order(BaseModel):
    id: str
    customer_name: str
    items: list[OrderItem]
    delivery_window: str  # e.g. "11:00-12:00"
    zone: str
    status: Literal["received", "picking", "picked", "dispatched", "delivered", "failed"]
    assigned_driver: Optional[str] = None
    timestamps: OrderTimestamps = Field(default_factory=OrderTimestamps)
    missing_items: list[str] = Field(default_factory=list)
    notes: str = ""
    risk_level: Literal["green", "yellow", "red"] = "green"
    # Large/heavy order flags
    items_picked: int = 0          # count of items picked so far (updated during picking)
    total_items: int = 0           # sum of all item quantities (computed on save)
    has_heavy_items: bool = False  # contains water cases, bulk, etc.
    needs_driver: bool = False     # too large/heavy for a biker (total_items > 15 or has_heavy_items)


class Driver(BaseModel):
    id: str
    name: str
    type: Literal["biker", "driver"]
    zones: list[str]
    status: Literal["available", "on_delivery", "called_out"]
    current_orders: list[str] = Field(default_factory=list)
    company: str = ""              # delivery company name


class Exception_(BaseModel):
    id: str
    type: Literal["late_risk", "missing_item", "coverage_gap", "delivery_dispute", "driver_reservation"]
    order_id: Optional[str] = None
    severity: Literal["low", "medium", "high"]
    description: str
    agent_recommendation: str
    status: Literal["open", "escalated", "resolved"] = "open"
    cs_notified: bool = False
    created_at: str
    resolved_at: Optional[str] = None


class CSNotification(BaseModel):
    id: str
    order_id: Optional[str] = None
    customer_name: Optional[str] = None
    issue_type: str
    details: str
    customer_message: str
    # pending_batch = staged, not yet shown to CS (will be batched when picking completes)
    # pending = ready for CS action
    # handled = CS has acted on it
    status: Literal["pending_batch", "pending", "handled"] = "pending"
    notification_subtype: Literal["immediate", "batched", "standard"] = "standard"
    created_at: str
    handled_at: Optional[str] = None


class AgentRunResult(BaseModel):
    status: str
    exceptions_detected: int
    notifications_created: int
    summary: str
    timestamp: str
