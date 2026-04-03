"""
Generate realistic test data for DispatchIQ.

Scenario: Mid-shift on a busy delivery day.
- 4 delivery windows: 10:00-11:00, 11:00-12:00, 12:00-13:00, 13:00-14:00
- 5 zones: Uptown, Midtown, Chelsea, East Village, Downtown
- 12 drivers: 8 bikers, 4 drivers
- Built-in exceptions:
    * 1 driver called out (Downtown uncovered)
    * 3 orders with missing items (1 core item)
    * 11am-12pm window overloaded — too many orders for capacity
    * Several orders behind schedule in the 11am window
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

MENU_ITEMS = [
    ("Salmon Fillet", True),
    ("Chicken Breast", True),
    ("Ribeye Steak", True),
    ("Tofu Block", True),
    ("Pork Tenderloin", True),
    ("Quinoa Mix", False),
    ("Roasted Vegetables", False),
    ("Brown Rice", False),
    ("Mixed Greens", False),
    ("Lemon Herb Sauce", False),
    ("Garlic Butter", False),
    ("Sweet Potato", False),
    ("Asparagus Bundle", False),
    ("Dinner Rolls", False),
    ("Sparkling Water", False),
    ("Red Wine (375ml)", False),
]

FIRST_NAMES = [
    "James", "Maria", "David", "Sarah", "Michael", "Jennifer", "Robert", "Emily",
    "William", "Ashley", "Richard", "Jessica", "Thomas", "Amanda", "Charles",
    "Melissa", "Daniel", "Stephanie", "Matthew", "Rebecca", "Anthony", "Laura",
    "Donald", "Helen", "Mark", "Sandra", "Paul", "Donna", "Steven", "Carol",
    "Andrew", "Ruth", "Kenneth", "Sharon", "Joshua", "Michelle", "Kevin", "Dorothy",
    "Brian", "Betty", "George", "Rachel", "Timothy", "Anna", "Ronald", "Christine",
    "Edward", "Megan", "Jason", "Alice",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen",
    "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera",
    "Campbell", "Mitchell", "Carter", "Roberts",
]


def make_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"


def customer_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def make_items(include_missing_core=False, include_missing_minor=False):
    core_item = random.choice([i for i in MENU_ITEMS if i[1]])
    sides = random.sample([i for i in MENU_ITEMS if not i[1]], k=random.randint(2, 4))

    items = [{"name": core_item[0], "quantity": 1, "is_core_item": True}]
    for side in sides:
        items.append({"name": side[0], "quantity": random.randint(1, 2), "is_core_item": False})

    missing = []
    if include_missing_core:
        missing = [core_item[0]]
    elif include_missing_minor:
        missing = [random.choice([i["name"] for i in items if not i["is_core_item"]])]

    return items, missing


def ts(base: datetime, offset_minutes: int) -> str:
    return (base + timedelta(minutes=offset_minutes)).isoformat()


def generate_drivers() -> list[dict]:
    now = datetime.now()
    drivers = []

    biker_configs = [
        # (name, zones, status)
        ("Carlos Reyes", ["Uptown", "Midtown"], "available"),
        ("Ana Flores", ["Uptown", "Midtown"], "on_delivery"),
        ("Marcus Webb", ["Midtown", "Chelsea"], "available"),
        ("Priya Nair", ["Chelsea", "East Village"], "available"),
        ("Devon Clarke", ["Chelsea", "East Village"], "on_delivery"),
        ("Kenji Tanaka", ["East Village", "Midtown"], "available"),
        ("Sofia Morales", ["Uptown"], "available"),
        ("Liam O'Brien", ["Midtown", "Chelsea"], "on_delivery"),
    ]

    driver_configs = [
        ("Marcus Brown", ["Downtown", "Midtown", "Chelsea"], "on_delivery"),
        ("Jasmine Wong", ["Downtown", "East Village"], "called_out"),  # ← called out, downtown uncovered
        ("Tyler Banks", ["Uptown", "Downtown", "Midtown"], "available"),
        ("Amara Osei", ["Downtown", "East Village", "Chelsea"], "on_delivery"),
    ]

    for cfg in biker_configs:
        drivers.append({
            "id": make_id("DRV"),
            "name": cfg[0],
            "type": "biker",
            "zones": cfg[1],
            "status": cfg[2],
            "current_orders": [],
        })

    for cfg in driver_configs:
        drivers.append({
            "id": make_id("DRV"),
            "name": cfg[0],
            "type": "driver",
            "zones": cfg[1],
            "status": cfg[2],
            "current_orders": [],
        })

    return drivers


def generate_orders(drivers: list[dict]) -> list[dict]:
    now = datetime.now()
    orders = []

    driver_map = {d["name"]: d["id"] for d in drivers}

    # Helper: pick a driver for a zone
    def pick_driver(zone: str, driver_type: str = None):
        eligible = [
            d["name"] for d in drivers
            if zone in d["zones"]
            and d["status"] in ("available", "on_delivery")
            and (driver_type is None or d["type"] == driver_type)
        ]
        return random.choice(eligible) if eligible else None

    # ── 10:00-11:00 window (mostly completed) ─────────────────────────────────
    for _ in range(12):
        zone = random.choice(ZONES)
        items, missing = make_items()
        orders.append({
            "id": make_id("ORD"),
            "customer_name": customer_name(),
            "items": items,
            "delivery_window": "10:00-11:00",
            "zone": zone,
            "status": random.choices(
                ["delivered", "dispatched", "delivered"],
                weights=[70, 20, 10], k=1
            )[0],
            "assigned_driver": pick_driver(zone),
            "timestamps": {
                "received": ts(now, -120),
                "picking_started": ts(now, -110),
                "picked": ts(now, -100),
                "dispatched": ts(now, -90),
                "delivered": ts(now, -75) if random.random() > 0.2 else None,
            },
            "missing_items": missing,
            "notes": "",
            "risk_level": "green",
        })

    # ── 11:00-12:00 window (active, OVERLOADED, several at risk) ──────────────
    # This window has too many orders — meant to trigger agent
    for i in range(20):  # Deliberately too many
        zone = random.choice(ZONES)
        items, missing = make_items()

        # Build in some at-risk orders (stuck in picking/received)
        if i < 7:
            status = random.choice(["picking", "received"])
        elif i < 13:
            status = "picked"
        elif i < 17:
            status = "dispatched"
        else:
            status = "delivered"

        orders.append({
            "id": make_id("ORD"),
            "customer_name": customer_name(),
            "items": items,
            "delivery_window": "11:00-12:00",
            "zone": zone,
            "status": status,
            "assigned_driver": pick_driver(zone),
            "timestamps": {
                "received": ts(now, -70),
                "picking_started": ts(now, -60) if status != "received" else None,
                "picked": ts(now, -40) if status in ("picked", "dispatched", "delivered") else None,
                "dispatched": ts(now, -20) if status in ("dispatched", "delivered") else None,
                "delivered": ts(now, -5) if status == "delivered" else None,
            },
            "missing_items": missing,
            "notes": "",
            "risk_level": "green",
        })

    # ── Missing items orders (built-in exceptions) ─────────────────────────────

    # Order with CORE item missing — highest priority
    core_missing_items, core_missing = make_items(include_missing_core=True)
    orders.append({
        "id": "ORD-CORE01",
        "customer_name": "Rachel Kim",
        "items": core_missing_items,
        "delivery_window": "11:00-12:00",
        "zone": "Midtown",
        "status": "picking",
        "assigned_driver": pick_driver("Midtown"),
        "timestamps": {
            "received": ts(now, -65),
            "picking_started": ts(now, -55),
            "picked": None,
            "dispatched": None,
            "delivered": None,
        },
        "missing_items": core_missing,
        "notes": "Picker flagged core item missing from cold storage",
        "risk_level": "green",
    })

    # Order with minor item missing
    minor_missing_items, minor_missing = make_items(include_missing_minor=True)
    orders.append({
        "id": "ORD-MINOR1",
        "customer_name": "David Chen",
        "items": minor_missing_items,
        "delivery_window": "11:00-12:00",
        "zone": "Chelsea",
        "status": "picked",
        "assigned_driver": pick_driver("Chelsea"),
        "timestamps": {
            "received": ts(now, -80),
            "picking_started": ts(now, -70),
            "picked": ts(now, -50),
            "dispatched": None,
            "delivered": None,
        },
        "missing_items": minor_missing,
        "notes": "",
        "risk_level": "green",
    })

    # Another minor missing
    minor_missing_items2, minor_missing2 = make_items(include_missing_minor=True)
    orders.append({
        "id": "ORD-MINOR2",
        "customer_name": "Sofia Gutiérrez",
        "items": minor_missing_items2,
        "delivery_window": "12:00-13:00",
        "zone": "East Village",
        "status": "picking",
        "assigned_driver": pick_driver("East Village"),
        "timestamps": {
            "received": ts(now, -40),
            "picking_started": ts(now, -30),
            "picked": None,
            "dispatched": None,
            "delivered": None,
        },
        "missing_items": minor_missing2,
        "notes": "",
        "risk_level": "green",
    })

    # ── 12:00-13:00 window (in progress) ──────────────────────────────────────
    for i in range(14):
        zone = random.choice(ZONES)
        items, _ = make_items()
        if i < 5:
            status = "received"
        elif i < 10:
            status = "picking"
        else:
            status = "picked"

        orders.append({
            "id": make_id("ORD"),
            "customer_name": customer_name(),
            "items": items,
            "delivery_window": "12:00-13:00",
            "zone": zone,
            "status": status,
            "assigned_driver": pick_driver(zone),
            "timestamps": {
                "received": ts(now, -35),
                "picking_started": ts(now, -25) if status != "received" else None,
                "picked": ts(now, -10) if status == "picked" else None,
                "dispatched": None,
                "delivered": None,
            },
            "missing_items": [],
            "notes": "",
            "risk_level": "green",
        })

    # ── 13:00-14:00 window (queued) ────────────────────────────────────────────
    for _ in range(8):
        zone = random.choice(ZONES)
        items, _ = make_items()
        orders.append({
            "id": make_id("ORD"),
            "customer_name": customer_name(),
            "items": items,
            "delivery_window": "13:00-14:00",
            "zone": zone,
            "status": "received",
            "assigned_driver": None,
            "timestamps": {
                "received": ts(now, -10),
                "picking_started": None,
                "picked": None,
                "dispatched": None,
                "delivered": None,
            },
            "missing_items": [],
            "notes": "",
            "risk_level": "green",
        })

    return orders


def generate_exceptions() -> list[dict]:
    """Pre-seed one known exception so the dashboard has something on load."""
    now = datetime.now()
    return [
        {
            "id": "EXC-PRELOAD1",
            "type": "coverage_gap",
            "order_id": None,
            "severity": "high",
            "description": "Jasmine Wong (driver, Downtown/East Village) called out. Downtown zone has 0 available drivers.",
            "agent_recommendation": "Reassign Downtown orders to Tyler Banks (driver). Alert dispatcher to find backup coverage for East Village.",
            "status": "open",
            "cs_notified": False,
            "created_at": (datetime.now() - timedelta(minutes=15)).isoformat(),
            "resolved_at": None,
        }
    ]


def main():
    print("🚚 Generating DispatchIQ test data...")

    drivers = generate_drivers()
    orders = generate_orders(drivers)
    exceptions = generate_exceptions()

    (DATA_DIR / "orders.json").write_text(json.dumps(orders, indent=2))
    (DATA_DIR / "drivers.json").write_text(json.dumps(drivers, indent=2))
    (DATA_DIR / "exceptions.json").write_text(json.dumps(exceptions, indent=2))
    (DATA_DIR / "cs_notifications.json").write_text(json.dumps([], indent=2))

    print(f"✅ {len(orders)} orders generated across {len(WINDOWS)} windows")
    print(f"✅ {len(drivers)} drivers ({sum(1 for d in drivers if d['type'] == 'biker')} bikers, {sum(1 for d in drivers if d['type'] == 'driver')} drivers)")
    print(f"✅ {len(exceptions)} pre-seeded exception (Downtown coverage gap)")
    print(f"✅ Built-in exceptions:")
    print(f"   • ORD-CORE01 — Rachel Kim, core item missing (should block dispatch)")
    print(f"   • ORD-MINOR1 — David Chen, minor item missing")
    print(f"   • ORD-MINOR2 — Sofia Gutiérrez, minor item missing")
    print(f"   • Jasmine Wong called out → Downtown zone uncovered")
    print(f"   • 11:00-12:00 window has {sum(1 for o in orders if o['delivery_window'] == '11:00-12:00')} orders (overloaded)")
    print()
    print("Run `python main.py` to start the backend, then trigger the agent at POST /agent/run")


if __name__ == "__main__":
    main()
