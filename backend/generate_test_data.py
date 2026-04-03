"""
Generate realistic test data for DispatchIQ.

Scenario: Active mid-morning shift.
- 4 windows: 10:00-11:00, 11:00-12:00, 12:00-13:00, 13:00-14:00
- 5 zones: Uptown, Midtown, Chelsea, East Village, Downtown
- 12 drivers across 3 companies
- Large/heavy orders requiring car drivers
- OOS scenarios (core + minor)
- Batched CS notification staging
"""

import json
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

random.seed(42)

ZONES = ["Uptown", "Midtown", "Chelsea", "East Village", "Downtown"]
WINDOWS = ["10:00-11:00", "11:00-12:00", "12:00-13:00", "13:00-14:00"]

# (name, is_core, is_heavy)
MENU_ITEMS = [
    ("Salmon Fillet", True, False),
    ("Chicken Breast", True, False),
    ("Ribeye Steak", True, False),
    ("Tofu Block", True, False),
    ("Pork Tenderloin", True, False),
    ("Quinoa Mix", False, False),
    ("Roasted Vegetables", False, False),
    ("Brown Rice", False, False),
    ("Mixed Greens", False, False),
    ("Lemon Herb Sauce", False, False),
    ("Garlic Butter", False, False),
    ("Sweet Potato", False, False),
    ("Asparagus Bundle", False, False),
    ("Dinner Rolls", False, False),
    ("Greek Yogurt", False, False),
    ("Strawberries", False, False),
    ("Sparkling Water", False, False),
    ("Red Wine (375ml)", False, False),
]

HEAVY_ITEMS = [
    ("Case Sparkling Water (12-pack)", False, True),
    ("Case Still Water (24-pack)", False, True),
    ("Bulk Rice (10lb)", False, True),
    ("Case Orange Juice (6-pack)", False, True),
    ("Case Soda (12-pack)", False, True),
]

FIRST_NAMES = [
    "James", "Maria", "David", "Sarah", "Michael", "Jennifer", "Robert", "Emily",
    "William", "Ashley", "Richard", "Jessica", "Thomas", "Amanda", "Charles",
    "Melissa", "Daniel", "Stephanie", "Matthew", "Rebecca", "Anthony", "Laura",
    "Donald", "Helen", "Mark", "Sandra", "Paul", "Donna", "Steven", "Carol",
    "Andrew", "Ruth", "Kenneth", "Sharon", "Joshua", "Michelle", "Kevin", "Dorothy",
    "Brian", "Betty", "George", "Rachel", "Timothy", "Anna", "Ronald", "Christine",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen",
]


def make_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"


def customer_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def make_standard_items():
    core = random.choice([i for i in MENU_ITEMS if i[1]])
    sides = random.sample([i for i in MENU_ITEMS if not i[1]], k=random.randint(2, 4))
    items = [{"name": core[0], "quantity": 1, "is_core_item": True, "is_heavy": False}]
    for s in sides:
        items.append({"name": s[0], "quantity": random.randint(1, 2), "is_core_item": False, "is_heavy": False})
    total_items = sum(i["quantity"] for i in items)
    return items, total_items, False, False


def make_large_items(with_heavy: bool = False):
    """Create a large order (20+ items, possibly with heavy items)."""
    core = random.choice([i for i in MENU_ITEMS if i[1]])
    items = [{"name": core[0], "quantity": 2, "is_core_item": True, "is_heavy": False}]
    sides = random.sample([i for i in MENU_ITEMS if not i[1]], k=6)
    for s in sides:
        items.append({"name": s[0], "quantity": random.randint(2, 4), "is_core_item": False, "is_heavy": False})
    if with_heavy:
        heavy = random.choice(HEAVY_ITEMS)
        items.append({"name": heavy[0], "quantity": 2, "is_core_item": False, "is_heavy": True})

    has_heavy = with_heavy
    total_items = sum(i["quantity"] for i in items)
    needs_driver = total_items > 15 or has_heavy
    return items, total_items, has_heavy, needs_driver


def ts(base: datetime, offset_minutes: int) -> str:
    return (base + timedelta(minutes=offset_minutes)).isoformat()


def generate_drivers() -> list[dict]:
    return [
        # ── QuickPedal Couriers (bikers, Uptown/Midtown) ──────────────────────
        {
            "id": make_id("DRV"), "name": "Carlos Reyes", "type": "biker",
            "zones": ["Uptown", "Midtown"], "status": "available",
            "current_orders": [], "company": "QuickPedal Couriers",
        },
        {
            "id": make_id("DRV"), "name": "Ana Flores", "type": "biker",
            "zones": ["Uptown", "Midtown"], "status": "on_delivery",
            "current_orders": [], "company": "QuickPedal Couriers",
        },
        {
            "id": make_id("DRV"), "name": "Sofia Morales", "type": "biker",
            "zones": ["Uptown"], "status": "available",
            "current_orders": [], "company": "QuickPedal Couriers",
        },

        # ── Metro Express (bikers, Chelsea/East Village/Midtown) ──────────────
        {
            "id": make_id("DRV"), "name": "Priya Nair", "type": "biker",
            "zones": ["Chelsea", "East Village"], "status": "available",
            "current_orders": [], "company": "Metro Express",
        },
        {
            "id": make_id("DRV"), "name": "Devon Clarke", "type": "biker",
            "zones": ["Chelsea", "East Village"], "status": "on_delivery",
            "current_orders": [], "company": "Metro Express",
        },
        {
            "id": make_id("DRV"), "name": "Kenji Tanaka", "type": "biker",
            "zones": ["East Village", "Midtown"], "status": "available",
            "current_orders": [], "company": "Metro Express",
        },
        {
            "id": make_id("DRV"), "name": "Marcus Webb", "type": "biker",
            "zones": ["Midtown", "Chelsea"], "status": "available",
            "current_orders": [], "company": "Metro Express",
        },
        {
            "id": make_id("DRV"), "name": "Liam O'Brien", "type": "biker",
            "zones": ["Midtown", "Chelsea"], "status": "on_delivery",
            "current_orders": [], "company": "Metro Express",
        },

        # ── Downtown Direct (car drivers, all Manhattan) ──────────────────────
        {
            "id": make_id("DRV"), "name": "Marcus Brown", "type": "driver",
            "zones": ["Downtown", "Midtown", "Chelsea"], "status": "on_delivery",
            "current_orders": [], "company": "Downtown Direct",
        },
        {
            "id": make_id("DRV"), "name": "Jasmine Wong", "type": "driver",
            "zones": ["Downtown", "East Village"], "status": "called_out",  # ← called out
            "current_orders": [], "company": "Downtown Direct",
        },
        {
            "id": make_id("DRV"), "name": "Tyler Banks", "type": "driver",
            "zones": ["Uptown", "Downtown", "Midtown"], "status": "available",
            "current_orders": [], "company": "Downtown Direct",
        },
        {
            "id": make_id("DRV"), "name": "Amara Osei", "type": "driver",
            "zones": ["Downtown", "East Village", "Chelsea"], "status": "on_delivery",
            "current_orders": [], "company": "Downtown Direct",
        },
    ]


def generate_orders(drivers: list[dict]) -> list[dict]:
    now = datetime.now()
    orders = []

    def pick_driver(zone: str, driver_type=None):
        eligible = [
            d["name"] for d in drivers
            if zone in d["zones"]
            and d["status"] in ("available", "on_delivery")
            and (driver_type is None or d["type"] == driver_type)
        ]
        return random.choice(eligible) if eligible else None

    # ── 10:00-11:00 (mostly complete) ─────────────────────────────────────────
    for _ in range(12):
        zone = random.choice(ZONES)
        items, total, has_heavy, needs_driver = make_standard_items()
        status = random.choices(["delivered", "dispatched"], weights=[80, 20])[0]
        orders.append({
            "id": make_id("ORD"), "customer_name": customer_name(),
            "items": items, "delivery_window": "10:00-11:00", "zone": zone,
            "status": status, "assigned_driver": pick_driver(zone),
            "timestamps": {
                "received": ts(now, -120), "picking_started": ts(now, -110),
                "picked": ts(now, -100), "dispatched": ts(now, -90),
                "delivered": ts(now, -75) if status == "delivered" else None,
            },
            "missing_items": [], "notes": "", "risk_level": "green",
            "items_picked": total, "total_items": total,
            "has_heavy_items": has_heavy, "needs_driver": needs_driver,
        })

    # ── 11:00-12:00 (active, overloaded) ──────────────────────────────────────
    for i in range(18):
        zone = random.choice(ZONES)
        items, total, has_heavy, needs_driver = make_standard_items()
        if i < 6:
            status = random.choice(["picking", "received"])
            items_picked = random.randint(0, max(1, total // 2)) if status == "picking" else 0
        elif i < 12:
            status = "picked"
            items_picked = total
        elif i < 16:
            status = "dispatched"
            items_picked = total
        else:
            status = "delivered"
            items_picked = total

        orders.append({
            "id": make_id("ORD"), "customer_name": customer_name(),
            "items": items, "delivery_window": "11:00-12:00", "zone": zone,
            "status": status, "assigned_driver": pick_driver(zone),
            "timestamps": {
                "received": ts(now, -70),
                "picking_started": ts(now, -60) if status != "received" else None,
                "picked": ts(now, -40) if status in ("picked", "dispatched", "delivered") else None,
                "dispatched": ts(now, -20) if status in ("dispatched", "delivered") else None,
                "delivered": ts(now, -5) if status == "delivered" else None,
            },
            "missing_items": [], "notes": "", "risk_level": "green",
            "items_picked": items_picked, "total_items": total,
            "has_heavy_items": has_heavy, "needs_driver": needs_driver,
        })

    # ── Specific exception orders ──────────────────────────────────────────────

    # CORE ITEM MISSING — blocks dispatch
    core_items = [
        {"name": "Pork Tenderloin", "quantity": 1, "is_core_item": True, "is_heavy": False},
        {"name": "Sweet Potato", "quantity": 2, "is_core_item": False, "is_heavy": False},
        {"name": "Roasted Vegetables", "quantity": 1, "is_core_item": False, "is_heavy": False},
    ]
    orders.append({
        "id": "ORD-CORE01", "customer_name": "Rachel Kim",
        "items": core_items, "delivery_window": "11:00-12:00", "zone": "Midtown",
        "status": "picking", "assigned_driver": pick_driver("Midtown"),
        "timestamps": {"received": ts(now, -65), "picking_started": ts(now, -55), "picked": None, "dispatched": None, "delivered": None},
        "missing_items": ["Pork Tenderloin"], "notes": "Core item missing from cold storage",
        "risk_level": "green", "items_picked": 3, "total_items": 4,
        "has_heavy_items": False, "needs_driver": False,
    })

    # MINOR OOS — will be batched when picking completes
    minor1_items = [
        {"name": "Chicken Breast", "quantity": 1, "is_core_item": True, "is_heavy": False},
        {"name": "Strawberries", "quantity": 2, "is_core_item": False, "is_heavy": False},
        {"name": "Greek Yogurt", "quantity": 1, "is_core_item": False, "is_heavy": False},
        {"name": "Mixed Greens", "quantity": 1, "is_core_item": False, "is_heavy": False},
    ]
    orders.append({
        "id": "ORD-MINOR1", "customer_name": "David Chen",
        "items": minor1_items, "delivery_window": "11:00-12:00", "zone": "Chelsea",
        "status": "picking", "assigned_driver": pick_driver("Chelsea"),
        "timestamps": {"received": ts(now, -70), "picking_started": ts(now, -60), "picked": None, "dispatched": None, "delivered": None},
        "missing_items": ["Strawberries", "Greek Yogurt"], "notes": "",
        "risk_level": "green", "items_picked": 3, "total_items": 5,
        "has_heavy_items": False, "needs_driver": False,
    })

    # ANOTHER MINOR OOS
    minor2_items = [
        {"name": "Salmon Fillet", "quantity": 1, "is_core_item": True, "is_heavy": False},
        {"name": "Red Wine (375ml)", "quantity": 1, "is_core_item": False, "is_heavy": False},
        {"name": "Asparagus Bundle", "quantity": 2, "is_core_item": False, "is_heavy": False},
    ]
    orders.append({
        "id": "ORD-MINOR2", "customer_name": "Sofia Gutiérrez",
        "items": minor2_items, "delivery_window": "12:00-13:00", "zone": "East Village",
        "status": "picking", "assigned_driver": pick_driver("East Village"),
        "timestamps": {"received": ts(now, -40), "picking_started": ts(now, -30), "picked": None, "dispatched": None, "delivered": None},
        "missing_items": ["Red Wine (375ml)"], "notes": "",
        "risk_level": "green", "items_picked": 2, "total_items": 4,
        "has_heavy_items": False, "needs_driver": False,
    })

    # LARGE ORDERS needing car drivers ─────────────────────────────────────────

    # Large + heavy — 11am window, Downtown
    large1_items, large1_total, large1_heavy, _ = make_large_items(with_heavy=True)
    orders.append({
        "id": "ORD-LARGE1", "customer_name": "James Rodriguez",
        "items": large1_items, "delivery_window": "11:00-12:00", "zone": "Downtown",
        "status": "picking", "assigned_driver": pick_driver("Downtown", "driver"),
        "timestamps": {"received": ts(now, -65), "picking_started": ts(now, -55), "picked": None, "dispatched": None, "delivered": None},
        "missing_items": [], "notes": "Bulk office order — includes water cases",
        "risk_level": "green", "items_picked": random.randint(5, 12), "total_items": large1_total,
        "has_heavy_items": True, "needs_driver": True,
    })

    # Large — 12pm window, Midtown (party order)
    large2_items, large2_total, _, _ = make_large_items(with_heavy=False)
    orders.append({
        "id": "ORD-LARGE2", "customer_name": "The Patel Group",
        "items": large2_items, "delivery_window": "12:00-13:00", "zone": "Midtown",
        "status": "received", "assigned_driver": None,
        "timestamps": {"received": ts(now, -30), "picking_started": None, "picked": None, "dispatched": None, "delivered": None},
        "missing_items": [], "notes": f"Party order — {large2_total} items",
        "risk_level": "green", "items_picked": 0, "total_items": large2_total,
        "has_heavy_items": False, "needs_driver": large2_total > 15,
    })

    # Large + heavy — 12pm window, Chelsea (monthly bulk)
    large3_items, large3_total, large3_heavy, _ = make_large_items(with_heavy=True)
    orders.append({
        "id": "ORD-LARGE3", "customer_name": "Chelsea Market Co.",
        "items": large3_items, "delivery_window": "12:00-13:00", "zone": "Chelsea",
        "status": "received", "assigned_driver": None,
        "timestamps": {"received": ts(now, -25), "picking_started": None, "picked": None, "dispatched": None, "delivered": None},
        "missing_items": [], "notes": "Monthly bulk — water cases included",
        "risk_level": "green", "items_picked": 0, "total_items": large3_total,
        "has_heavy_items": True, "needs_driver": True,
    })

    # Large — 1pm window, Uptown
    large4_items, large4_total, _, _ = make_large_items(with_heavy=False)
    orders.append({
        "id": "ORD-LARGE4", "customer_name": "Uptown Catering LLC",
        "items": large4_items, "delivery_window": "13:00-14:00", "zone": "Uptown",
        "status": "received", "assigned_driver": None,
        "timestamps": {"received": ts(now, -10), "picking_started": None, "picked": None, "dispatched": None, "delivered": None},
        "missing_items": [], "notes": f"Catering order — {large4_total} items",
        "risk_level": "green", "items_picked": 0, "total_items": large4_total,
        "has_heavy_items": False, "needs_driver": large4_total > 15,
    })

    # ── 12:00-13:00 (in progress) ──────────────────────────────────────────────
    for i in range(12):
        zone = random.choice(ZONES)
        items, total, has_heavy, needs_driver = make_standard_items()
        status = "received" if i < 4 else "picking" if i < 9 else "picked"
        items_picked = random.randint(0, total - 1) if status == "picking" else (total if status == "picked" else 0)
        orders.append({
            "id": make_id("ORD"), "customer_name": customer_name(),
            "items": items, "delivery_window": "12:00-13:00", "zone": zone,
            "status": status, "assigned_driver": pick_driver(zone),
            "timestamps": {
                "received": ts(now, -35),
                "picking_started": ts(now, -25) if status != "received" else None,
                "picked": ts(now, -10) if status == "picked" else None,
                "dispatched": None, "delivered": None,
            },
            "missing_items": [], "notes": "", "risk_level": "green",
            "items_picked": items_picked, "total_items": total,
            "has_heavy_items": has_heavy, "needs_driver": needs_driver,
        })

    # ── 13:00-14:00 (queued) ──────────────────────────────────────────────────
    for _ in range(7):
        zone = random.choice(ZONES)
        items, total, has_heavy, needs_driver = make_standard_items()
        orders.append({
            "id": make_id("ORD"), "customer_name": customer_name(),
            "items": items, "delivery_window": "13:00-14:00", "zone": zone,
            "status": "received", "assigned_driver": None,
            "timestamps": {"received": ts(now, -8), "picking_started": None, "picked": None, "dispatched": None, "delivered": None},
            "missing_items": [], "notes": "", "risk_level": "green",
            "items_picked": 0, "total_items": total,
            "has_heavy_items": has_heavy, "needs_driver": needs_driver,
        })

    return orders


def generate_exceptions() -> list[dict]:
    now = datetime.now()
    return [
        {
            "id": "EXC-PRELOAD1",
            "type": "coverage_gap",
            "order_id": None,
            "severity": "high",
            "description": "Jasmine Wong (driver, Downtown Direct) called out. Downtown zone has 1 remaining driver.",
            "agent_recommendation": "Tyler Banks is the only remaining Downtown Direct driver. Prioritize him for Downtown and large orders. Flag upcoming large Downtown orders (ORD-LARGE1) for immediate assignment.",
            "status": "open",
            "cs_notified": False,
            "created_at": (datetime.now() - timedelta(minutes=15)).isoformat(),
            "resolved_at": None,
        },
        {
            "id": "EXC-PRELOAD2",
            "type": "driver_reservation",
            "order_id": "ORD-LARGE2",
            "severity": "medium",
            "description": "Large order ORD-LARGE2 (The Patel Group, 12pm-1pm, Midtown) requires a car driver. Currently unassigned.",
            "agent_recommendation": "Assign Tyler Banks or ensure Marcus Brown returns in time. Do not commit Tyler to small orders during 11:30am-12:00pm window.",
            "status": "open",
            "cs_notified": False,
            "created_at": (datetime.now() - timedelta(minutes=10)).isoformat(),
            "resolved_at": None,
        },
    ]


def generate_cs_notifications() -> list[dict]:
    """Pre-seed pending_batch notifications for the minor OOS orders."""
    now = datetime.now()
    return [
        # Staged (pending_batch) for ORD-MINOR1 — Strawberries
        {
            "id": "CS-BATCH01",
            "order_id": "ORD-MINOR1",
            "customer_name": "David Chen",
            "issue_type": "oos_minor",
            "details": "OOS during picking: Strawberries",
            "customer_message": "Your Strawberries were unavailable — will be batched with other OOS items.",
            "status": "pending_batch",
            "notification_subtype": "standard",
            "created_at": (datetime.now() - timedelta(minutes=8)).isoformat(),
            "handled_at": None,
        },
        # Staged (pending_batch) for ORD-MINOR1 — Greek Yogurt
        {
            "id": "CS-BATCH02",
            "order_id": "ORD-MINOR1",
            "customer_name": "David Chen",
            "issue_type": "oos_minor",
            "details": "OOS during picking: Greek Yogurt",
            "customer_message": "Your Greek Yogurt was unavailable — will be batched with other OOS items.",
            "status": "pending_batch",
            "notification_subtype": "standard",
            "created_at": (datetime.now() - timedelta(minutes=7)).isoformat(),
            "handled_at": None,
        },
        # Staged (pending_batch) for ORD-MINOR2 — Red Wine
        {
            "id": "CS-BATCH03",
            "order_id": "ORD-MINOR2",
            "customer_name": "Sofia Gutiérrez",
            "issue_type": "oos_minor",
            "details": "OOS during picking: Red Wine (375ml)",
            "customer_message": "Your Red Wine was unavailable — will be batched with other OOS items.",
            "status": "pending_batch",
            "notification_subtype": "standard",
            "created_at": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "handled_at": None,
        },
        # IMMEDIATE for ORD-CORE01 — core item missing
        {
            "id": "CS-IMMED01",
            "order_id": "ORD-CORE01",
            "customer_name": "Rachel Kim",
            "issue_type": "missing_core_item",
            "details": "Core item Pork Tenderloin missing from cold storage. Order cannot be dispatched as-is.",
            "customer_message": "Hi Rachel, we're sorry — your Pork Tenderloin is currently unavailable. We can offer a substitution (Chicken Breast or Salmon Fillet) or a full refund for that item. Please reply or call us to let us know your preference before we dispatch your order.",
            "status": "pending",
            "notification_subtype": "immediate",
            "created_at": (datetime.now() - timedelta(minutes=12)).isoformat(),
            "handled_at": None,
        },
    ]


def main():
    print("🚚 Generating DispatchIQ test data...")

    drivers = generate_drivers()
    orders = generate_orders(drivers)
    exceptions = generate_exceptions()
    cs_notifications = generate_cs_notifications()

    (DATA_DIR / "orders.json").write_text(json.dumps(orders, indent=2))
    (DATA_DIR / "drivers.json").write_text(json.dumps(drivers, indent=2))
    (DATA_DIR / "exceptions.json").write_text(json.dumps(exceptions, indent=2))
    (DATA_DIR / "cs_notifications.json").write_text(json.dumps(cs_notifications, indent=2))

    large = [o for o in orders if o["needs_driver"]]
    print(f"✅ {len(orders)} orders across {len(WINDOWS)} windows")
    print(f"✅ {len(drivers)} drivers: QuickPedal (3), Metro Express (5), Downtown Direct (4)")
    print(f"✅ {len(large)} large/heavy orders requiring car drivers:")
    for o in large:
        print(f"   • {o['id']} — {o['customer_name']} — {o['delivery_window']} — {o['total_items']} items {'(HEAVY)' if o['has_heavy_items'] else ''}")
    print(f"✅ {len(exceptions)} pre-seeded exceptions")
    print(f"✅ {len(cs_notifications)} CS notifications ({sum(1 for n in cs_notifications if n['status'] == 'pending')} immediate, {sum(1 for n in cs_notifications if n['status'] == 'pending_batch')} batched-pending)")
    print()
    print("Key scenarios:")
    print("  • ORD-CORE01: Rachel Kim — Pork Tenderloin missing (CORE) → immediate CS notification")
    print("  • ORD-MINOR1: David Chen — Strawberries + Greek Yogurt OOS → pending batch")
    print("  • ORD-MINOR2: Sofia Gutiérrez — Red Wine OOS → pending batch")
    print("  • Jasmine Wong called out → Downtown Direct running on 1 driver")
    print("  • 4 large/heavy orders across windows → driver reservation alerts")
    print("  • 11am window has 20 orders (overloaded)")


if __name__ == "__main__":
    main()
