from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class OrderItem(BaseModel):
    name: str
    quantity: int
    is_core_item: bool = False


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


class Driver(BaseModel):
    id: str
    name: str
    type: Literal["biker", "driver"]
    zones: list[str]
    status: Literal["available", "on_delivery", "called_out"]
    current_orders: list[str] = Field(default_factory=list)


class Exception_(BaseModel):
    id: str
    type: Literal["late_risk", "missing_item", "coverage_gap", "delivery_dispute"]
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
    status: Literal["pending", "handled"] = "pending"
    created_at: str
    handled_at: Optional[str] = None


class AgentRunResult(BaseModel):
    status: str
    exceptions_detected: int
    notifications_created: int
    summary: str
    timestamp: str
