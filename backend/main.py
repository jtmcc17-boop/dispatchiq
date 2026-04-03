from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import data_store
from models import Order, Driver, Exception_, CSNotification, AgentRunResult
from agent import AgentMonitor, run_agent_cycle, generate_shift_summary_text, compute_risk_level

# ─── App lifecycle ─────────────────────────────────────────────────────────────

agent_monitor = AgentMonitor(interval_seconds=60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(agent_monitor.run_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="DispatchIQ API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request bodies ────────────────────────────────────────────────────────────

class OrderStatusUpdate(BaseModel):
    status: str
    driver_id: Optional[str] = None
    missing_items: Optional[list[str]] = None
    notes: Optional[str] = None


class DriverStatusUpdate(BaseModel):
    status: str


class ExceptionUpdate(BaseModel):
    status: str


class CSNotificationUpdate(BaseModel):
    status: str


# ─── Orders ───────────────────────────────────────────────────────────────────

@app.get("/orders")
def list_orders(window: Optional[str] = None, zone: Optional[str] = None):
    orders = data_store.get_orders()
    now = datetime.now()

    # Compute risk levels
    result = []
    for o in orders:
        o_dict = o.model_dump()
        o_dict["risk_level"] = compute_risk_level(o, now)
        result.append(o_dict)

    if window:
        result = [o for o in result if o["delivery_window"] == window]
    if zone:
        result = [o for o in result if o["zone"] == zone]

    return result


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = data_store.get_order(order_id)
    if not order:
        raise HTTPException(404, f"Order {order_id} not found")
    o_dict = order.model_dump()
    o_dict["risk_level"] = compute_risk_level(order, datetime.now())
    return o_dict


@app.patch("/orders/{order_id}")
def update_order(order_id: str, update: OrderStatusUpdate):
    now_iso = datetime.now().isoformat()
    updates = {"status": update.status}

    # Auto-set timestamps
    ts_map = {
        "picking": "picking_started",
        "picked": "picked",
        "dispatched": "dispatched",
        "delivered": "delivered",
    }
    if update.status in ts_map:
        updates["timestamps"] = {ts_map[update.status]: now_iso}

    if update.missing_items is not None:
        updates["missing_items"] = update.missing_items
    if update.notes is not None:
        updates["notes"] = update.notes
    if update.driver_id:
        driver = data_store.get_driver(update.driver_id)
        if driver:
            updates["assigned_driver"] = driver.name

    order = data_store.update_order(order_id, updates)
    if not order:
        raise HTTPException(404, f"Order {order_id} not found")
    return order.model_dump()


# ─── Drivers ──────────────────────────────────────────────────────────────────

@app.get("/drivers")
def list_drivers():
    return [d.model_dump() for d in data_store.get_drivers()]


@app.patch("/drivers/{driver_id}")
def update_driver(driver_id: str, update: DriverStatusUpdate):
    driver = data_store.update_driver(driver_id, {"status": update.status})
    if not driver:
        raise HTTPException(404, f"Driver {driver_id} not found")
    return driver.model_dump()


# ─── Exceptions ───────────────────────────────────────────────────────────────

@app.get("/exceptions")
def list_exceptions(status: Optional[str] = None):
    exceptions = data_store.get_exceptions()
    if status:
        exceptions = [e for e in exceptions if e.status == status]
    return [e.model_dump() for e in exceptions]


@app.patch("/exceptions/{exc_id}")
def update_exception(exc_id: str, update: ExceptionUpdate):
    updates = {"status": update.status}
    if update.status == "resolved":
        updates["resolved_at"] = datetime.now().isoformat()
    exc = data_store.update_exception(exc_id, updates)
    if not exc:
        raise HTTPException(404, f"Exception {exc_id} not found")
    return exc.model_dump()


# ─── CS Notifications ─────────────────────────────────────────────────────────

@app.get("/cs-notifications")
def list_cs_notifications(status: Optional[str] = None):
    notifications = data_store.get_cs_notifications()
    if status:
        notifications = [n for n in notifications if n.status == status]
    return [n.model_dump() for n in notifications]


@app.patch("/cs-notifications/{notif_id}")
def update_cs_notification(notif_id: str, update: CSNotificationUpdate):
    updates = {"status": update.status}
    if update.status == "handled":
        updates["handled_at"] = datetime.now().isoformat()
    notif = data_store.update_cs_notification(notif_id, updates)
    if not notif:
        raise HTTPException(404, f"Notification {notif_id} not found")
    return notif.model_dump()


# ─── Agent ────────────────────────────────────────────────────────────────────

@app.post("/agent/run")
def run_agent():
    """Trigger an immediate agent monitoring cycle."""
    try:
        result = run_agent_cycle()
        return result
    except Exception as e:
        raise HTTPException(500, f"Agent error: {str(e)}")


@app.get("/agent/status")
def agent_status():
    return agent_monitor.get_status()


@app.get("/agent/shift-summary")
async def shift_summary():
    """Generate an end-of-shift narrative summary."""
    try:
        text = await generate_shift_summary_text()
        stats = data_store.get_exceptions()
        return {
            "summary": text,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(500, f"Summary error: {str(e)}")


# ─── Stats ────────────────────────────────────────────────────────────────────

@app.get("/stats")
def get_stats():
    orders = data_store.get_orders()
    drivers = data_store.get_drivers()
    exceptions = data_store.get_exceptions()
    notifications = data_store.get_cs_notifications()
    now = datetime.now()

    status_counts = {}
    for o in orders:
        status_counts[o.status] = status_counts.get(o.status, 0) + 1

    windows = sorted(set(o.delivery_window for o in orders))
    window_stats = {}
    for w in windows:
        w_orders = [o for o in orders if o.delivery_window == w]
        at_risk = [o for o in w_orders if compute_risk_level(o, now) in ("yellow", "red")]
        window_stats[w] = {
            "total": len(w_orders),
            "delivered": sum(1 for o in w_orders if o.status == "delivered"),
            "dispatched": sum(1 for o in w_orders if o.status == "dispatched"),
            "at_risk": len(at_risk),
        }

    return {
        "total_orders": len(orders),
        "status_breakdown": status_counts,
        "window_stats": window_stats,
        "drivers": {
            "total": len(drivers),
            "available": sum(1 for d in drivers if d.status == "available"),
            "on_delivery": sum(1 for d in drivers if d.status == "on_delivery"),
            "called_out": sum(1 for d in drivers if d.status == "called_out"),
        },
        "open_exceptions": sum(1 for e in exceptions if e.status == "open"),
        "pending_notifications": sum(1 for n in notifications if n.status == "pending"),
    }


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat()}
