"""
Ocean Freight Rate & Shipment Tracker - Main Application
Built with FastAPI, SQLite, and Tailwind CSS.
Supports all 4 Core Modules + Authentication + Bonus Requirements.
"""

import os
import json
import csv
import io
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, Response, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import database
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user_from_request, require_auth, require_admin
)
from email_parser import parse_email, parse_email_inbox

# Ensure database is initialized
database.init_db()

app = FastAPI(
    title="Ocean Freight Rate & Shipment Tracker",
    description="Digitize • Optimize • Democratize ocean freight rates, shipments, invoices, and email parsing.",
    version="1.0.0"
)

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

USD_TO_INR_RATE = 83.50  # Standard reference FX rate


# -----------------------------------------------------------------------------
# PYDANTIC SCHEMAS
# -----------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "user"  # 'admin' or 'user'

class RateCreateRequest(BaseModel):
    carrier: str
    origin_port: str
    destination_port: str
    container_type: str
    rate_usd: float
    transit_days: int

class ShipmentCreateRequest(BaseModel):
    shipment_id: str
    carrier: str
    origin_port: str
    destination_port: str
    container_type: str
    departure_date: str
    expected_arrival: str
    delivered_date: Optional[str] = None
    invoice_amount_usd: Optional[float] = None
    status_notes: Optional[str] = None

class ShipmentUpdateRequest(BaseModel):
    carrier: Optional[str] = None
    origin_port: Optional[str] = None
    destination_port: Optional[str] = None
    container_type: Optional[str] = None
    departure_date: Optional[str] = None
    expected_arrival: Optional[str] = None
    delivered_date: Optional[str] = None
    invoice_amount_usd: Optional[float] = None
    status_override: Optional[str] = None
    status_notes: Optional[str] = None

class InvoiceCheckRequest(BaseModel):
    shipment_id: str
    invoice_amount_usd: float
    currency: Optional[str] = "USD"

class ParseCustomEmailRequest(BaseModel):
    email_text: str
    apply_to_db: Optional[bool] = False


# -----------------------------------------------------------------------------
# AUTHENTICATION ENDPOINTS
# -----------------------------------------------------------------------------

@app.post("/api/auth/login")
async def login(req: LoginRequest, response: Response):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (req.username.strip(),))
    user = cursor.fetchone()
    conn.close()

    if not user or not verify_password(req.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    user_data = {
        "id": user['id'],
        "username": user['username'],
        "role": user['role'],
        "full_name": user['full_name']
    }
    token = create_access_token(user_data)

    # Set secure cookie
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        max_age=86400 * 7,
        samesite="lax"
    )

    return {
        "success": True,
        "token": token,
        "user": user_data
    }


@app.post("/api/auth/register")
async def register(req: RegisterRequest, response: Response):
    """Register a new user account with securely hashed credentials and store in database."""
    username = req.username.strip().lower()
    if not username or len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )
    if not req.password or len(req.password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 4 characters long"
        )

    role = req.role if req.role in ("admin", "user") else "user"
    full_name = (req.full_name or "").strip() or username.capitalize()

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{username}' already exists. Please choose a different username or log in."
        )

    pw_hash = hash_password(req.password)
    cursor.execute("""
        INSERT INTO users (username, password_hash, role, full_name)
        VALUES (?, ?, ?, ?)
    """, (username, pw_hash, role, full_name))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    user_data = {
        "id": user_id,
        "username": username,
        "role": role,
        "full_name": full_name
    }
    token = create_access_token(user_data)

    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        max_age=86400 * 7,
        samesite="lax"
    )

    return {
        "success": True,
        "token": token,
        "user": user_data,
        "message": f"Account for {full_name} ({role.upper()}) created and credentials saved successfully."
    }


@app.get("/api/auth/me")
async def get_current_user(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user}


@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key="token")
    return {"success": True, "message": "Logged out successfully"}


# -----------------------------------------------------------------------------
# MODULE 1: RATE SEARCH ENDPOINTS
# -----------------------------------------------------------------------------

@app.get("/api/rates/ports")
async def get_ports():
    """Retrieve distinct origin and destination ports for dropdown menus."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT origin_port FROM carrier_rates ORDER BY origin_port")
    origins = [r['origin_port'] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT destination_port FROM carrier_rates ORDER BY destination_port")
    destinations = [r['destination_port'] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT origin_port, destination_port FROM carrier_rates ORDER BY origin_port, destination_port")
    routes_by_origin = {}
    for r in cursor.fetchall():
        routes_by_origin.setdefault(r['origin_port'], []).append(r['destination_port'])

    cursor.execute("SELECT DISTINCT carrier FROM carrier_rates ORDER BY carrier")
    carriers = [r['carrier'] for r in cursor.fetchall()]
    conn.close()

    return {
        "origin_ports": origins,
        "destination_ports": destinations,
        "routes_by_origin": routes_by_origin,
        "carriers": carriers,
        "container_types": ["20ft", "40ft"]
    }


@app.get("/api/rates/search")
async def search_rates(
    origin_port: str = Query(...),
    destination_port: str = Query(...),
    container_type: str = Query(...),
    sort_by: str = Query("price")  # 'price' or 'transit'
):
    """
    Search carrier rates matching route and container type.
    Highlights cheapest carrier, calculates savings, and provides transit times.
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()

    order_clause = "ORDER BY rate_usd ASC" if sort_by == "price" else "ORDER BY transit_days ASC, rate_usd ASC"
    cursor.execute(f"""
        SELECT * FROM carrier_rates
        WHERE origin_port = ? AND destination_port = ? AND container_type = ?
        {order_clause}
    """, (origin_port.strip(), destination_port.strip(), container_type.strip()))

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not rows:
        return {
            "origin_port": origin_port,
            "destination_port": destination_port,
            "container_type": container_type,
            "results_count": 0,
            "cheapest_carrier": None,
            "results": []
        }

    # Find cheapest price
    cheapest_rate = min(r['rate_usd'] for r in rows)
    highest_rate = max(r['rate_usd'] for r in rows)
    avg_rate = sum(r['rate_usd'] for r in rows) / len(rows)

    cheapest_carrier_info = None
    for r in rows:
        is_cheapest = (r['rate_usd'] == cheapest_rate)
        r['is_cheapest'] = is_cheapest
        r['rate_inr'] = round(r['rate_usd'] * USD_TO_INR_RATE, 2)
        r['potential_savings_usd'] = round(highest_rate - r['rate_usd'], 2)
        r['savings_vs_avg_usd'] = round(avg_rate - r['rate_usd'], 2)
        if is_cheapest and not cheapest_carrier_info:
            cheapest_carrier_info = r

    return {
        "origin_port": origin_port,
        "destination_port": destination_port,
        "container_type": container_type,
        "results_count": len(rows),
        "cheapest_carrier": cheapest_carrier_info,
        "max_savings_usd": round(highest_rate - cheapest_rate, 2),
        "avg_rate_usd": round(avg_rate, 2),
        "results": rows
    }


@app.post("/api/rates")
async def create_or_update_rate(req: RateCreateRequest, request: Request):
    """Admin-only: Insert or update a contracted carrier rate."""
    user = require_admin(request)
    conn = database.get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO carrier_rates 
        (carrier, origin_port, destination_port, container_type, rate_usd, transit_days, source, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'manual', CURRENT_TIMESTAMP)
        ON CONFLICT(carrier, origin_port, destination_port, container_type) 
        DO UPDATE SET 
            rate_usd = excluded.rate_usd,
            transit_days = excluded.transit_days,
            source = 'manual',
            updated_at = CURRENT_TIMESTAMP
    """, (
        req.carrier.strip(),
        req.origin_port.strip(),
        req.destination_port.strip(),
        req.container_type.strip(),
        req.rate_usd,
        req.transit_days
    ))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Rate updated successfully"}


# -----------------------------------------------------------------------------
# MODULE 2: SHIPMENT TRACKER ENDPOINTS
# -----------------------------------------------------------------------------

@app.get("/api/shipments")
async def list_shipments(
    status_filter: Optional[str] = Query(None),
    carrier_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    reference_date: Optional[str] = Query(None)
):
    """
    List all shipments with dynamic status calculation (In Transit, Delivered, Delayed).
    Supports status filter, carrier filter, and search.
    """
    all_shipments = database.get_all_shipments_with_computed_status(reference_date)

    filtered = []
    for s in all_shipments:
        if status_filter and status_filter.lower() != 'all':
            if s['computed_status'].lower() != status_filter.lower():
                continue

        if carrier_filter and carrier_filter.lower() != 'all':
            if s['carrier'].lower() != carrier_filter.lower():
                continue

        if search:
            query = search.lower()
            match = (
                query in s['shipment_id'].lower() or
                query in s['carrier'].lower() or
                query in s['origin_port'].lower() or
                query in s['destination_port'].lower()
            )
            if not match:
                continue

        filtered.append(s)

    return {
        "count": len(filtered),
        "total": len(all_shipments),
        "reference_date": reference_date or datetime.today().strftime('%Y-%m-%d'),
        "shipments": filtered
    }


@app.get("/api/shipments/stats")
async def shipment_stats(reference_date: Optional[str] = None):
    """Bonus feature: Aggregated shipment statistics for visual dashboard & charts."""
    all_shipments = database.get_all_shipments_with_computed_status(reference_date)

    status_counts = {"Delivered": 0, "In Transit": 0, "Delayed": 0}
    carrier_counts = {}
    overcharged_count = 0
    total_overcharge_usd = 0.0

    for s in all_shipments:
        st = s['computed_status']
        status_counts[st] = status_counts.get(st, 0) + 1

        c = s['carrier']
        carrier_counts[c] = carrier_counts.get(c, 0) + 1

        if s.get('invoice_status') == 'OVERCHARGED':
            overcharged_count += 1
            total_overcharge_usd += (s.get('discrepancy_usd') or 0.0)

    return {
        "total_shipments": len(all_shipments),
        "status_distribution": status_counts,
        "carrier_distribution": carrier_counts,
        "overcharged_count": overcharged_count,
        "total_overcharge_usd": round(total_overcharge_usd, 2),
        "total_overcharge_inr": round(total_overcharge_usd * USD_TO_INR_RATE, 2)
    }


@app.post("/api/shipments")
async def add_shipment(req: ShipmentCreateRequest, request: Request):
    """Add a new shipment to the tracking system."""
    user = require_auth(request)
    conn = database.get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO shipments (
                shipment_id, carrier, origin_port, destination_port, container_type,
                departure_date, expected_arrival, delivered_date, invoice_amount_usd, status_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            req.shipment_id.strip().upper(),
            req.carrier.strip(),
            req.origin_port.strip(),
            req.destination_port.strip(),
            req.container_type.strip(),
            req.departure_date.strip(),
            req.expected_arrival.strip(),
            req.delivered_date.strip() if req.delivered_date else None,
            req.invoice_amount_usd,
            req.status_notes
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"Shipment ID '{req.shipment_id.upper()}' already exists."
        )
    finally:
        conn.close()

    return {"success": True, "message": f"Shipment {req.shipment_id.upper()} added successfully"}


@app.put("/api/shipments/{shipment_id}")
async def update_shipment(shipment_id: str, req: ShipmentUpdateRequest, request: Request):
    """Update shipment details or status."""
    user = require_auth(request)
    conn = database.get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM shipments WHERE shipment_id = ?", (shipment_id.upper(),))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Shipment not found")

    fields = []
    values = []
    for k, v in req.dict(exclude_unset=True).items():
        if v is not None:
            fields.append(f"{k} = ?")
            values.append(v)

    if fields:
        values.append(shipment_id.upper())
        cursor.execute(f"""
            UPDATE shipments 
            SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE shipment_id = ?
        """, tuple(values))
        conn.commit()

    conn.close()
    return {"success": True, "message": f"Shipment {shipment_id.upper()} updated"}


@app.post("/api/shipments/{shipment_id}/deliver")
async def mark_delivered(shipment_id: str, request: Request, delivery_date: Optional[str] = None):
    """Quick action: Mark shipment as Delivered."""
    user = require_auth(request)
    deliv_date = delivery_date or datetime.today().strftime('%Y-%m-%d')
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE shipments 
        SET delivered_date = ?, status_override = 'Delivered', updated_at = CURRENT_TIMESTAMP
        WHERE shipment_id = ?
    """, (deliv_date, shipment_id.upper()))
    conn.commit()
    conn.close()

    return {"success": True, "message": f"Shipment {shipment_id.upper()} marked as Delivered on {deliv_date}"}


@app.delete("/api/shipments/{shipment_id}")
async def delete_shipment(shipment_id: str, request: Request):
    """Admin-only: Remove a shipment."""
    user = require_admin(request)
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shipments WHERE shipment_id = ?", (shipment_id.upper(),))
    conn.commit()
    conn.close()

    return {"success": True, "message": f"Shipment {shipment_id.upper()} deleted"}


@app.get("/api/shipments/export")
async def export_shipments(format: str = Query("csv")):
    """Bonus feature: Export shipments to Excel/CSV with calculated status and billing flags."""
    shipments = database.get_all_shipments_with_computed_status()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Shipment ID", "Carrier", "Origin Port", "Destination Port", "Container Type",
        "Departure Date", "Expected Arrival", "Delivered Date", "Status",
        "Contracted Rate (USD)", "Invoiced Amount (USD)", "Discrepancy (USD)", "Audit Status"
    ])

    for s in shipments:
        writer.writerow([
            s['shipment_id'],
            s['carrier'],
            s['origin_port'],
            s['destination_port'],
            s['container_type'],
            s['departure_date'],
            s['expected_arrival'],
            s.get('delivered_date') or "N/A",
            s['computed_status'],
            s.get('contracted_rate_usd') or "N/A",
            s.get('invoice_amount_usd') or "N/A",
            s.get('discrepancy_usd') if s.get('discrepancy_usd') is not None else "N/A",
            s.get('invoice_status') or "N/A"
        ])

    output.seek(0)
    filename = f"ocean_shipments_{datetime.today().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# -----------------------------------------------------------------------------
# MODULE 3: INVOICE CHECKER ENDPOINTS
# -----------------------------------------------------------------------------

@app.post("/api/invoice/check")
async def check_invoice(req: InvoiceCheckRequest):
    """
    Check an invoice against the contracted rate for a shipment.
    Shows 'Correct' or 'Overcharged by INR/USD X' (or undercharged).
    """
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, r.rate_usd as contracted_rate_usd
        FROM shipments s
        LEFT JOIN carrier_rates r 
          ON s.carrier = r.carrier 
         AND s.origin_port = r.origin_port 
         AND s.destination_port = r.destination_port 
         AND s.container_type = r.container_type
        WHERE s.shipment_id = ?
    """, (req.shipment_id.strip().upper(),))
    shipment = cursor.fetchone()

    if not shipment:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Shipment '{req.shipment_id.upper()}' was not found in the database."
        )

    contracted_usd = shipment['contracted_rate_usd']
    if contracted_usd is None:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"No matching contracted rate found for {shipment['carrier']} on {shipment['origin_port']} -> {shipment['destination_port']} ({shipment['container_type']})."
        )

    invoiced_usd = float(req.invoice_amount_usd)
    diff_usd = round(invoiced_usd - contracted_usd, 2)
    diff_inr = round(diff_usd * USD_TO_INR_RATE, 2)
    pct_diff = round(((invoiced_usd - contracted_usd) / contracted_usd) * 100, 2)

    if diff_usd > 0:
        verdict = "OVERCHARGED"
        status_message = f"Overcharged by USD ${diff_usd:,.2f} (₹{diff_inr:,.2f})"
        color = "red"
    elif diff_usd < 0:
        verdict = "UNDERCHARGED"
        status_message = f"Undercharged / Discounted by USD ${abs(diff_usd):,.2f} (₹{abs(diff_inr):,.2f})"
        color = "blue"
    else:
        verdict = "CORRECT"
        status_message = "Correct (Exact match with contracted rate)"
        color = "green"

    # Log to audit history
    cursor.execute("""
        INSERT INTO invoice_audit (
            shipment_id, carrier, route, container_type,
            invoiced_amount_usd, contracted_rate_usd, discrepancy_usd, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        shipment['shipment_id'],
        shipment['carrier'],
        f"{shipment['origin_port']} -> {shipment['destination_port']}",
        shipment['container_type'],
        invoiced_usd,
        contracted_usd,
        diff_usd,
        verdict
    ))
    conn.commit()
    conn.close()

    return {
        "shipment_id": shipment['shipment_id'],
        "carrier": shipment['carrier'],
        "origin_port": shipment['origin_port'],
        "destination_port": shipment['destination_port'],
        "container_type": shipment['container_type'],
        "contracted_rate_usd": contracted_usd,
        "contracted_rate_inr": round(contracted_usd * USD_TO_INR_RATE, 2),
        "invoiced_amount_usd": invoiced_usd,
        "invoiced_amount_inr": round(invoiced_usd * USD_TO_INR_RATE, 2),
        "discrepancy_usd": diff_usd,
        "discrepancy_inr": diff_inr,
        "percentage_difference": pct_diff,
        "verdict": verdict,
        "status_message": status_message,
        "color": color
    }


@app.get("/api/invoice/audit-all")
async def audit_all_shipments():
    """Run an automated audit across all sample shipments with invoices."""
    shipments = database.get_all_shipments_with_computed_status()

    audited = []
    total_overcharge = 0.0
    total_undercharge = 0.0
    correct_count = 0
    overcharged_count = 0
    undercharged_count = 0

    for s in shipments:
        inv = s.get('invoice_amount_usd')
        contract = s.get('contracted_rate_usd')
        if inv is not None and contract is not None:
            diff = round(inv - contract, 2)
            pct = round((diff / contract) * 100, 2)
            item = {
                "shipment_id": s['shipment_id'],
                "carrier": s['carrier'],
                "route": f"{s['origin_port']} -> {s['destination_port']}",
                "container_type": s['container_type'],
                "contracted_rate_usd": contract,
                "invoiced_amount_usd": inv,
                "discrepancy_usd": diff,
                "discrepancy_inr": round(diff * USD_TO_INR_RATE, 2),
                "pct_diff": pct,
                "status": "OVERCHARGED" if diff > 0 else ("UNDERCHARGED" if diff < 0 else "CORRECT")
            }
            if diff > 0:
                overcharged_count += 1
                total_overcharge += diff
            elif diff < 0:
                undercharged_count += 1
                total_undercharge += abs(diff)
            else:
                correct_count += 1

            audited.append(item)

    return {
        "audited_count": len(audited),
        "correct_count": correct_count,
        "overcharged_count": overcharged_count,
        "undercharged_count": undercharged_count,
        "total_overcharge_usd": round(total_overcharge, 2),
        "total_overcharge_inr": round(total_overcharge * USD_TO_INR_RATE, 2),
        "total_undercharge_usd": round(total_undercharge, 2),
        "items": audited
    }


# -----------------------------------------------------------------------------
# MODULE 4: EMAIL-BASED RATE & SHIPMENT UPDATES
# -----------------------------------------------------------------------------

@app.get("/api/emails/inbox")
async def get_sample_inbox():
    """Retrieve raw emails from sample_emails.txt for preview and analysis."""
    sample_file = os.path.join(DATA_DIR, "sample_emails.txt")
    if not os.path.exists(sample_file):
        raise HTTPException(status_code=404, detail="sample_emails.txt not found")

    parsed_list = parse_email_inbox(sample_file)
    return {
        "count": len(parsed_list),
        "emails": parsed_list
    }


@app.post("/api/emails/parse-all")
async def parse_and_apply_emails(apply_to_db: bool = Query(True), request: Request = None):
    """
    Parse all sample emails and automatically apply rate updates and shipment status updates.
    Gracefully skips irrelevant emails (marketing, OOO, malformed).
    """
    sample_file = os.path.join(DATA_DIR, "sample_emails.txt")
    if not os.path.exists(sample_file):
        raise HTTPException(status_code=404, detail="sample_emails.txt not found")

    parsed_items = parse_email_inbox(sample_file)
    conn = database.get_db_connection()
    cursor = conn.cursor()

    applied_rates = []
    applied_shipments = []
    skipped_emails = []

    for item in parsed_items:
        email_idx = item['email_index']
        p_type = item['type']
        p_action = item['action']
        data = item['extracted_data']

        if p_type == 'rate_update' and apply_to_db:
            carrier = data['carrier']
            origin = data['origin_port']
            dest = data['destination_port']
            container = data['container_type']
            new_rate = data['rate_usd']

            # Check previous rate
            cursor.execute("""
                SELECT rate_usd, transit_days FROM carrier_rates 
                WHERE carrier = ? AND origin_port = ? AND destination_port = ? AND container_type = ?
            """, (carrier, origin, dest, container))
            prev = cursor.fetchone()
            prev_rate = prev['rate_usd'] if prev else None
            transit = prev['transit_days'] if prev else 30

            cursor.execute("""
                INSERT INTO carrier_rates 
                (carrier, origin_port, destination_port, container_type, rate_usd, transit_days, source, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'email_update', CURRENT_TIMESTAMP)
                ON CONFLICT(carrier, origin_port, destination_port, container_type) 
                DO UPDATE SET 
                    rate_usd = excluded.rate_usd,
                    source = 'email_update',
                    updated_at = CURRENT_TIMESTAMP
            """, (carrier, origin, dest, container, new_rate, transit))

            applied_rates.append({
                "email_index": email_idx,
                "carrier": carrier,
                "route": f"{origin} -> {dest}",
                "container_type": container,
                "previous_rate_usd": prev_rate,
                "new_rate_usd": new_rate,
                "change_usd": round(new_rate - (prev_rate or new_rate), 2)
            })

        elif p_type == 'shipment_update' and apply_to_db:
            shp_id = data['shipment_id']
            new_status = data['status']
            deliv_date = data.get('delivered_date')
            notes = data.get('notes')

            cursor.execute("SELECT * FROM shipments WHERE shipment_id = ?", (shp_id,))
            existing = cursor.fetchone()

            if existing:
                prev_status = database.calculate_shipment_status(dict(existing))
                update_fields = ["status_override = ?", "updated_at = CURRENT_TIMESTAMP"]
                params = [new_status]

                if deliv_date:
                    update_fields.append("delivered_date = ?")
                    params.append(deliv_date)

                if notes:
                    update_fields.append("status_notes = ?")
                    params.append(notes)

                params.append(shp_id)
                cursor.execute(f"UPDATE shipments SET {', '.join(update_fields)} WHERE shipment_id = ?", tuple(params))

                applied_shipments.append({
                    "email_index": email_idx,
                    "shipment_id": shp_id,
                    "previous_status": prev_status,
                    "new_status": new_status,
                    "delivered_date": deliv_date,
                    "notes": notes
                })

        else:
            skipped_emails.append({
                "email_index": email_idx,
                "subject": item['headers'].get('Subject'),
                "sender": item['headers'].get('From'),
                "reason": item['reason']
            })

        # Save email log
        cursor.execute("""
            INSERT INTO email_logs 
            (email_index, sender, subject, email_date, body, parsed_type, parsed_action, reason, extracted_json, applied)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email_idx,
            item['headers'].get('From'),
            item['headers'].get('Subject'),
            item['headers'].get('Date'),
            item['body'],
            p_type,
            p_action,
            item['reason'],
            json.dumps(data),
            1 if apply_to_db and p_action != 'skip' else 0
        ))

    conn.commit()
    conn.close()

    return {
        "total_emails_parsed": len(parsed_items),
        "rates_updated_count": len(applied_rates),
        "shipments_updated_count": len(applied_shipments),
        "skipped_emails_count": len(skipped_emails),
        "applied_rates": applied_rates,
        "applied_shipments": applied_shipments,
        "skipped_emails": skipped_emails
    }


@app.post("/api/emails/parse-single")
async def parse_single_email_text(req: ParseCustomEmailRequest):
    """
    Test individual email plain text in real-time.
    Demonstrates interactive NLP entity extraction playground.
    """
    parsed = parse_email(req.email_text, email_index=0)
    applied = False

    if req.apply_to_db and parsed['action'] != 'skip':
        conn = database.get_db_connection()
        cursor = conn.cursor()
        data = parsed['extracted_data']

        if parsed['type'] == 'rate_update':
            cursor.execute("""
                INSERT INTO carrier_rates 
                (carrier, origin_port, destination_port, container_type, rate_usd, transit_days, source, updated_at)
                VALUES (?, ?, ?, ?, ?, 30, 'custom_email', CURRENT_TIMESTAMP)
                ON CONFLICT(carrier, origin_port, destination_port, container_type) 
                DO UPDATE SET rate_usd = excluded.rate_usd, source = 'custom_email', updated_at = CURRENT_TIMESTAMP
            """, (data['carrier'], data['origin_port'], data['destination_port'], data['container_type'], data['rate_usd']))
            conn.commit()
            applied = True

        elif parsed['type'] == 'shipment_update':
            shp_id = data['shipment_id']
            cursor.execute("SELECT * FROM shipments WHERE shipment_id = ?", (shp_id,))
            if cursor.fetchone():
                update_fields = ["status_override = ?", "updated_at = CURRENT_TIMESTAMP"]
                params = [data['status']]
                if data.get('delivered_date'):
                    update_fields.append("delivered_date = ?")
                    params.append(data['delivered_date'])
                if data.get('notes'):
                    update_fields.append("status_notes = ?")
                    params.append(data['notes'])
                params.append(shp_id)
                cursor.execute(f"UPDATE shipments SET {', '.join(update_fields)} WHERE shipment_id = ?", tuple(params))
                conn.commit()
                applied = True

        conn.close()

    return {
        "parsed_result": parsed,
        "applied_to_db": applied
    }


# -----------------------------------------------------------------------------
# SYSTEM & DEMO MANAGEMENT
# -----------------------------------------------------------------------------

@app.post("/api/system/reset")
async def reset_demo_data(request: Request):
    """Reset database to fresh initial CSV state."""
    database.reset_to_sample_data()
    return {"success": True, "message": "Database reset to pristine sample data."}


# -----------------------------------------------------------------------------
# FRONTEND PAGES
# -----------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Serve main interactive dashboard application."""
    user = get_current_user_from_request(request)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": user,
            "usd_to_inr": USD_TO_INR_RATE
        }
    )


@app.get("/presentation", response_class=HTMLResponse)
async def serve_presentation(request: Request):
    """Serve the 3-slide interactive presentation."""
    presentation_path = os.path.join(BASE_DIR, "presentation", "slides.html")
    if os.path.exists(presentation_path):
        with open(presentation_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Presentation deck loading...</h1>")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
