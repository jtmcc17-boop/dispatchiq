from __future__ import annotations

"""
DispatchIQ Agent — Claude-powered operations monitor.

The agent uses tool_use to inspect order state, detect exceptions,
and generate CS notifications. It runs in a background loop.
"""

import json
import uuid
import asyncio
from datetime import datetime, time
from typing import Any

import anthropic

import data_store
from models import Exception_, CSNotification, Order

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"

# ─── Risk calculation helpers ─────────────────────────────────────────────────

def _parse_window(window: str) -> tuple[time, time]:
    """Parse '11:00-12:00' into (start_time, end_time)."""
    start_str, end_str = window.split("-")
    start_h, start_m = map(int, start_str.split(":"))
    end_h, end_m = map(int, end_str.split(":"))
    return time(start_h, start_m), time(end_h, end_m)


def compute_risk_level(order: Order, now: datetime) -> str:
    """Return 'green', 'yellow', or 'red' based on window timing."""
    if order.status in ("delivered", "failed"):
        return "green"
    if order.status == "dispatched":
        return "green"

    try:
        start_t, end_t = _parse_window(order.delivery_window)
    except Exception:
        return "green"

    now_t = now.time()
    start = datetime.combine(now.date(), start_t)
    end = datetime.combine(now.date(), end_t)
    now_dt = now

    minutes_into_window = (now_dt - start).total_seconds() / 60
    minutes_to_end = (end - now_dt).total_seconds() / 60

    if now_dt < start:
        return "green"  # window hasn't started

    # Red: past window end and not dispatched
    if now_dt >= end and order.status not in ("dispatched", "delivered"):
        return "red"

    # Red: deep into window and still picking/received
    if minutes_into_window > 30 and order.status in ("received", "picking"):
        return "red"

    # Yellow: 15+ minutes in and still not picked
    if minutes_into_window > 15 and order.status in ("received", "picking"):
        return "yellow"

    # Yellow: past mid-window and not dispatched
    if minutes_to_end < 20 and order.status in ("received", "picking", "picked"):
        return "yellow"

    return "green"


# ─── Tool implementations ─────────────────────────────────────────────────────

def tool_check_window_risk(delivery_window: str) -> dict:
    """Analyze all orders in a window and return risk metrics."""
    orders = data_store.get_orders()
    window_orders = [o for o in orders if o.delivery_window == delivery_window]

    if not window_orders:
        return {"window": delivery_window, "total": 0, "at_risk": [], "message": "No orders in this window"}

    now = datetime.now()
    at_risk = []
    status_counts = {}

    for order in window_orders:
        risk = compute_risk_level(order, now)
        status_counts[order.status] = status_counts.get(order.status, 0) + 1
        if risk in ("yellow", "red"):
            at_risk.append({
                "order_id": order.id,
                "customer": order.customer_name,
                "status": order.status,
                "risk": risk,
                "zone": order.zone,
                "assigned_driver": order.assigned_driver,
            })

    drivers = data_store.get_drivers()
    available_drivers = [
        d for d in drivers
        if d.status == "available"
    ]

    return {
        "window": delivery_window,
        "total_orders": len(window_orders),
        "status_breakdown": status_counts,
        "at_risk_count": len(at_risk),
        "at_risk_orders": at_risk,
        "available_drivers": len(available_drivers),
        "risk_assessment": (
            "HIGH" if len(at_risk) > 3 else
            "MEDIUM" if len(at_risk) > 1 else
            "LOW"
        ),
    }


def tool_flag_missing_item(order_id: str, item_name: str) -> dict:
    """Evaluate criticality of a missing item."""
    order = data_store.get_order(order_id)
    if not order:
        return {"error": f"Order {order_id} not found"}

    item = next((i for i in order.items if i.name.lower() == item_name.lower()), None)
    if not item:
        # Check if it's in missing_items list
        is_core = False
        item_label = item_name
    else:
        is_core = item.is_core_item
        item_label = item.name

    return {
        "order_id": order_id,
        "customer": order.customer_name,
        "item": item_label,
        "is_core_item": is_core,
        "order_status": order.status,
        "severity": "high" if is_core else "low",
        "recommendation": (
            "CRITICAL: Do not dispatch. Notify CS immediately. Offer substitution or cancellation."
            if is_core else
            "Log and notify CS post-delivery. Order can proceed if customer is informed."
        ),
    }


def tool_check_driver_coverage(zone: str) -> dict:
    """Check driver availability for a zone."""
    drivers = data_store.get_drivers()
    zone_drivers = [d for d in drivers if zone in d.zones]
    available = [d for d in zone_drivers if d.status == "available"]
    called_out = [d for d in zone_drivers if d.status == "called_out"]
    on_delivery = [d for d in zone_drivers if d.status == "on_delivery"]

    orders = data_store.get_orders()
    pending_in_zone = [
        o for o in orders
        if o.zone == zone and o.status not in ("delivered", "failed", "dispatched")
    ]

    return {
        "zone": zone,
        "total_drivers": len(zone_drivers),
        "available": len(available),
        "on_delivery": len(on_delivery),
        "called_out": len(called_out),
        "called_out_names": [d.name for d in called_out],
        "pending_orders_in_zone": len(pending_in_zone),
        "coverage_status": (
            "CRITICAL" if len(available) == 0 and len(pending_in_zone) > 0 else
            "AT_RISK" if len(available) < len(pending_in_zone) / 3 else
            "OK"
        ),
        "available_driver_names": [f"{d.name} ({d.type})" for d in available],
    }


def tool_create_exception(
    exc_type: str,
    severity: str,
    description: str,
    agent_recommendation: str,
    order_id: str = None,
) -> dict:
    """Create an exception record."""
    exc = Exception_(
        id=f"EXC-{uuid.uuid4().hex[:8].upper()}",
        type=exc_type,
        order_id=order_id,
        severity=severity,
        description=description,
        agent_recommendation=agent_recommendation,
        status="open",
        cs_notified=False,
        created_at=datetime.now().isoformat(),
    )
    result = data_store.create_exception(exc)
    return {"exception_id": result.id, "created": result.id == exc.id, "duplicate": result.id != exc.id}


def tool_generate_cs_notification(
    order_id: str,
    issue_type: str,
    customer_message: str,
    details: str,
) -> dict:
    """Generate a CS notification."""
    order = data_store.get_order(order_id)
    customer_name = order.customer_name if order else "Unknown Customer"

    notif = CSNotification(
        id=f"CS-{uuid.uuid4().hex[:8].upper()}",
        order_id=order_id,
        customer_name=customer_name,
        issue_type=issue_type,
        details=details,
        customer_message=customer_message,
        status="pending",
        created_at=datetime.now().isoformat(),
    )
    result = data_store.create_cs_notification(notif)
    return {
        "notification_id": result.id,
        "created": result.id == notif.id,
        "duplicate": result.id != notif.id,
        "customer": customer_name,
    }


def tool_generate_shift_summary() -> dict:
    """Compile shift statistics for the summary."""
    orders = data_store.get_orders()
    exceptions = data_store.get_exceptions()
    notifications = data_store.get_cs_notifications()

    status_counts = {}
    for o in orders:
        status_counts[o.status] = status_counts.get(o.status, 0) + 1

    open_exceptions = [e for e in exceptions if e.status == "open"]
    resolved_exceptions = [e for e in exceptions if e.status == "resolved"]
    pending_notifications = [n for n in notifications if n.status == "pending"]

    windows = sorted(set(o.delivery_window for o in orders))
    window_stats = {}
    now = datetime.now()
    for w in windows:
        w_orders = [o for o in orders if o.delivery_window == w]
        late = [o for o in w_orders if compute_risk_level(o, now) == "red"]
        window_stats[w] = {
            "total": len(w_orders),
            "delivered": sum(1 for o in w_orders if o.status == "delivered"),
            "late_or_at_risk": len(late),
        }

    return {
        "total_orders": len(orders),
        "status_breakdown": status_counts,
        "window_stats": window_stats,
        "open_exceptions": len(open_exceptions),
        "resolved_exceptions": len(resolved_exceptions),
        "pending_cs_notifications": len(pending_notifications),
        "exception_types": {e.type: sum(1 for ex in open_exceptions if ex.type == e.type) for e in open_exceptions},
    }


# ─── Tool dispatcher ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "check_window_risk",
        "description": "Calculate whether orders in a delivery window are at risk of being late. Returns status breakdown, at-risk orders, and available driver count.",
        "input_schema": {
            "type": "object",
            "properties": {
                "delivery_window": {
                    "type": "string",
                    "description": "Window string like '11:00-12:00'",
                }
            },
            "required": ["delivery_window"],
        },
    },
    {
        "name": "flag_missing_item",
        "description": "Evaluate the criticality of a missing item in an order and recommend action.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "item_name": {"type": "string"},
            },
            "required": ["order_id", "item_name"],
        },
    },
    {
        "name": "check_driver_coverage",
        "description": "Check driver availability and coverage gaps for a delivery zone.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone": {"type": "string", "description": "Zone name, e.g. 'Downtown'"},
            },
            "required": ["zone"],
        },
    },
    {
        "name": "create_exception",
        "description": "Create an exception record for an operational issue detected during monitoring.",
        "input_schema": {
            "type": "object",
            "properties": {
                "exc_type": {
                    "type": "string",
                    "enum": ["late_risk", "missing_item", "coverage_gap", "delivery_dispute"],
                },
                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                "description": {"type": "string"},
                "agent_recommendation": {"type": "string"},
                "order_id": {"type": "string", "description": "Optional order ID if tied to specific order"},
            },
            "required": ["exc_type", "severity", "description", "agent_recommendation"],
        },
    },
    {
        "name": "generate_cs_notification",
        "description": "Create a notification for the CS queue about an order issue. MUST be used when a core item is missing, an order will definitely be late, or a delivery dispute is logged.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "issue_type": {"type": "string"},
                "customer_message": {
                    "type": "string",
                    "description": "The message CS should relay to the customer",
                },
                "details": {"type": "string", "description": "Internal details for the CS rep"},
            },
            "required": ["order_id", "issue_type", "customer_message", "details"],
        },
    },
    {
        "name": "generate_shift_summary",
        "description": "Compile current shift statistics — total orders, delivery rates, open exceptions, pending CS notifications.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def dispatch_tool(tool_name: str, tool_input: dict) -> Any:
    if tool_name == "check_window_risk":
        return tool_check_window_risk(tool_input["delivery_window"])
    elif tool_name == "flag_missing_item":
        return tool_flag_missing_item(tool_input["order_id"], tool_input["item_name"])
    elif tool_name == "check_driver_coverage":
        return tool_check_driver_coverage(tool_input["zone"])
    elif tool_name == "create_exception":
        return tool_create_exception(**tool_input)
    elif tool_name == "generate_cs_notification":
        return tool_generate_cs_notification(**tool_input)
    elif tool_name == "generate_shift_summary":
        return tool_generate_shift_summary()
    else:
        return {"error": f"Unknown tool: {tool_name}"}


# ─── Main agent loop ──────────────────────────────────────────────────────────

def build_monitoring_prompt() -> str:
    orders = data_store.get_orders()
    drivers = data_store.get_drivers()
    now = datetime.now()

    # Update risk levels
    active_orders = [o for o in orders if o.status not in ("delivered", "failed")]
    windows = sorted(set(o.delivery_window for o in active_orders))

    # Find orders with missing items not yet flagged
    orders_with_missing = [o for o in orders if o.missing_items and o.status not in ("delivered", "failed")]

    # Called-out drivers
    called_out = [d for d in drivers if d.status == "called_out"]

    # Zones with active orders
    active_zones = sorted(set(o.zone for o in active_orders))

    prompt = f"""You are DispatchIQ, an agentic operations monitor for a last-mile delivery company.
Current time: {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}

Your job is to:
1. Check every active delivery window for late-risk orders
2. Flag any orders with missing items (especially core items — do NOT let those ship without CS notification)
3. Check driver coverage for all active zones
4. Create exceptions and CS notifications for any issues found
5. Do NOT create duplicate exceptions for issues already flagged

ACTIVE DELIVERY WINDOWS: {', '.join(windows) if windows else 'None'}
ORDERS WITH MISSING ITEMS: {json.dumps([{'id': o.id, 'customer': o.customer_name, 'missing': o.missing_items, 'status': o.status} for o in orders_with_missing])}
CALLED-OUT DRIVERS: {', '.join(d.name for d in called_out) if called_out else 'None'}
ACTIVE ZONES: {', '.join(active_zones) if active_zones else 'None'}

Use your tools to systematically check each window, each zone, and each order with missing items.
After your analysis, provide a concise ops summary of what you found and what actions you took."""

    return prompt


def run_agent_cycle() -> dict:
    """Run one full agent monitoring cycle. Returns summary dict."""
    prompt = build_monitoring_prompt()

    messages = [{"role": "user", "content": prompt}]
    exceptions_before = len(data_store.get_exceptions())
    notifications_before = len(data_store.get_cs_notifications())

    # Agentic loop
    final_text = ""
    max_iterations = 20
    iterations = 0

    while iterations < max_iterations:
        iterations += 1
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            tools=TOOLS,
            messages=messages,
        )

        # Collect tool uses from this response
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if text_blocks:
            final_text = text_blocks[-1].text

        if response.stop_reason == "end_turn" or not tool_uses:
            break

        # Add assistant message
        messages.append({"role": "assistant", "content": response.content})

        # Execute all tools and build tool results
        tool_results = []
        for tool_use in tool_uses:
            result = dispatch_tool(tool_use.name, tool_use.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps(result),
            })

        messages.append({"role": "user", "content": tool_results})

    exceptions_after = len(data_store.get_exceptions())
    notifications_after = len(data_store.get_cs_notifications())

    return {
        "status": "completed",
        "exceptions_detected": exceptions_after - exceptions_before,
        "notifications_created": notifications_after - notifications_before,
        "summary": final_text or "Agent cycle completed.",
        "timestamp": datetime.now().isoformat(),
    }


async def generate_shift_summary_text() -> str:
    """Ask Claude to write a formatted shift summary narrative."""
    stats = tool_generate_shift_summary()
    exceptions = data_store.get_exceptions()
    notifications = data_store.get_cs_notifications()

    prompt = f"""You are DispatchIQ. Generate a concise end-of-shift operations briefing.

Shift Statistics:
{json.dumps(stats, indent=2)}

Open Exceptions ({len([e for e in exceptions if e.status == 'open'])}):
{json.dumps([{'type': e.type, 'severity': e.severity, 'description': e.description} for e in exceptions if e.status == 'open'], indent=2)}

Pending CS Notifications ({len([n for n in notifications if n.status == 'pending'])}):
{json.dumps([{'order_id': n.order_id, 'issue': n.issue_type} for n in notifications if n.status == 'pending'], indent=2)}

Write a structured briefing for the next shift manager. Include:
- Overall shift performance (orders completed, rate)
- Issues that were handled
- Open items that need follow-up
- Any patterns worth noting
Keep it tight — ops managers read fast. Use bullet points."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ─── Background monitor ────────────────────────────────────────────────────────

class AgentMonitor:
    def __init__(self, interval_seconds: int = 45):
        self.interval = interval_seconds
        self.last_result: dict = {}
        self.running = False

    async def run_loop(self):
        self.running = True
        while self.running:
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, run_agent_cycle)
                self.last_result = result
            except Exception as e:
                self.last_result = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            await asyncio.sleep(self.interval)

    def get_status(self) -> dict:
        return self.last_result
