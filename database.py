"""
Database layer for Ocean Freight Rate & Shipment Tracker
Uses SQLite with optimized indexes and automated seeding from provided CSVs.
"""

import sqlite3
import csv
import os
import shutil
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from auth import hash_password

# Serverless environment (e.g. Vercel) has a read-only root filesystem, but /tmp is writable.
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/freight_tracker.db"
    _bundled_db = os.path.join(os.path.dirname(__file__), "freight_tracker.db")
    if not os.path.exists(DB_PATH) and os.path.exists(_bundled_db):
        try:
            shutil.copy2(_bundled_db, DB_PATH)
        except Exception:
            pass
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "freight_tracker.db")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def get_db_connection():
    """Returns a SQLite connection with Row factory enabled for dict-like access."""
    # Ensure DB directory exists if custom path
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force_reset: bool = False):
    """Initialize SQLite tables and indexes."""
    if force_reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users table (Admin & User roles with hashed passwords)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
        full_name TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Carrier Rates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS carrier_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        carrier TEXT NOT NULL,
        origin_port TEXT NOT NULL,
        destination_port TEXT NOT NULL,
        container_type TEXT NOT NULL CHECK(container_type IN ('20ft', '40ft')),
        rate_usd REAL NOT NULL,
        transit_days INTEGER NOT NULL,
        source TEXT DEFAULT 'initial_csv',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(carrier, origin_port, destination_port, container_type)
    );
    """)

    # 3. Shipments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shipments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_id TEXT UNIQUE NOT NULL,
        carrier TEXT NOT NULL,
        origin_port TEXT NOT NULL,
        destination_port TEXT NOT NULL,
        container_type TEXT NOT NULL CHECK(container_type IN ('20ft', '40ft')),
        departure_date TEXT NOT NULL,
        expected_arrival TEXT NOT NULL,
        delivered_date TEXT,
        invoice_amount_usd REAL,
        status_override TEXT,
        status_notes TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Email parsing logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_index INTEGER NOT NULL,
        sender TEXT,
        subject TEXT,
        email_date TEXT,
        body TEXT,
        parsed_type TEXT,
        parsed_action TEXT,
        reason TEXT,
        extracted_json TEXT,
        applied INTEGER DEFAULT 0,
        processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Invoice audit logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoice_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_id TEXT NOT NULL,
        carrier TEXT,
        route TEXT,
        container_type TEXT,
        invoiced_amount_usd REAL NOT NULL,
        contracted_rate_usd REAL NOT NULL,
        discrepancy_usd REAL NOT NULL,
        status TEXT NOT NULL,
        checked_by TEXT DEFAULT 'user',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rates_route ON carrier_rates(origin_port, destination_port, container_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_shipments_carrier ON shipments(carrier);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_shipments_id ON shipments(shipment_id);")

    conn.commit()
    conn.close()

    # Seed initial data
    seed_users()
    seed_carrier_rates()
    seed_shipments()


def seed_users():
    """Seed initial Admin and User accounts with securely hashed passwords."""
    conn = get_db_connection()
    cursor = conn.cursor()

    users_to_seed = [
        ("admin", "admin123", "admin", "Alex Morgan (Admin)"),
        ("user", "user123", "user", "Priya Sharma (Logistics Ops)")
    ]

    for username, plain_pw, role, full_name in users_to_seed:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            pw_hash = hash_password(plain_pw)
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, full_name)
                VALUES (?, ?, ?, ?)
            """, (username, pw_hash, role, full_name))

    conn.commit()
    conn.close()


def seed_carrier_rates():
    """Seed carrier rates from carrier_rates.csv."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM carrier_rates")
    if cursor.fetchone()['count'] == 0:
        csv_path = os.path.join(DATA_DIR, "carrier_rates.csv")
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute("""
                        INSERT OR REPLACE INTO carrier_rates 
                        (carrier, origin_port, destination_port, container_type, rate_usd, transit_days, source)
                        VALUES (?, ?, ?, ?, ?, ?, 'initial_csv')
                    """, (
                        row['carrier'].strip(),
                        row['origin_port'].strip(),
                        row['destination_port'].strip(),
                        row['container_type'].strip(),
                        float(row['rate_usd']),
                        int(row['transit_days'])
                    ))
            conn.commit()
    conn.close()


def seed_shipments():
    """Seed shipments from sample_shipments.csv."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM shipments")
    if cursor.fetchone()['count'] == 0:
        csv_path = os.path.join(DATA_DIR, "sample_shipments.csv")
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    delivered = row.get('delivered_date', '').strip() or None
                    inv_amt = row.get('invoice_amount_usd', '').strip()
                    invoice_amount = float(inv_amt) if inv_amt else None

                    cursor.execute("""
                        INSERT OR REPLACE INTO shipments
                        (shipment_id, carrier, origin_port, destination_port, container_type,
                         departure_date, expected_arrival, delivered_date, invoice_amount_usd)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['shipment_id'].strip(),
                        row['carrier'].strip(),
                        row['origin_port'].strip(),
                        row['destination_port'].strip(),
                        row['container_type'].strip(),
                        row['departure_date'].strip(),
                        row['expected_arrival'].strip(),
                        delivered,
                        invoice_amount
                    ))
            conn.commit()
    conn.close()


def calculate_shipment_status(shipment: Dict[str, Any], reference_date_str: Optional[str] = None) -> str:
    """
    Determine shipment status: 'Delivered', 'Delayed', or 'In Transit'.
    Rule:
    1. If delivered_date is present -> 'Delivered'
    2. If status_override is 'Delayed' (from email alert or admin flag) -> 'Delayed'
    3. If status_override is 'Delivered' -> 'Delivered'
    4. If today's date > expected_arrival and not delivered -> 'Delayed'
    5. Otherwise -> 'In Transit'
    """
    if shipment.get('delivered_date'):
        return 'Delivered'

    override = shipment.get('status_override')
    if override in ('Delayed', 'Delivered'):
        return override

    ref_date = reference_date_str or datetime.today().strftime('%Y-%m-%d')
    expected = shipment.get('expected_arrival', '')

    if expected and ref_date > expected:
        return 'Delayed'

    if override == 'In Transit':
        return 'In Transit'

    return 'In Transit'


def get_all_shipments_with_computed_status(reference_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all shipments with dynamically computed status and contracted rates."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.*, 
               r.rate_usd as contracted_rate_usd,
               r.transit_days as standard_transit_days
        FROM shipments s
        LEFT JOIN carrier_rates r 
          ON s.carrier = r.carrier 
         AND s.origin_port = r.origin_port 
         AND s.destination_port = r.destination_port 
         AND s.container_type = r.container_type
        ORDER BY s.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        item = dict(row)
        item['computed_status'] = calculate_shipment_status(item, reference_date)
        
        # Calculate invoice discrepancy if invoiced
        inv = item.get('invoice_amount_usd')
        contract = item.get('contracted_rate_usd')
        if inv is not None and contract is not None:
            diff = round(inv - contract, 2)
            item['discrepancy_usd'] = diff
            if diff > 0:
                item['invoice_status'] = 'OVERCHARGED'
            elif diff < 0:
                item['invoice_status'] = 'UNDERCHARGED'
            else:
                item['invoice_status'] = 'CORRECT'
        else:
            item['discrepancy_usd'] = None
            item['invoice_status'] = 'PENDING'

        result.append(item)

    return result


def find_contracted_rate(carrier: str, origin_port: str, destination_port: str, container_type: str) -> Optional[float]:
    """Find the exact contracted rate from carrier_rates table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT rate_usd FROM carrier_rates
        WHERE carrier = ? AND origin_port = ? AND destination_port = ? AND container_type = ?
    """, (carrier, origin_port, destination_port, container_type))
    row = cursor.fetchone()
    conn.close()
    return row['rate_usd'] if row else None


def reset_to_sample_data():
    """Resets database back to default sample state."""
    init_db(force_reset=True)
