"""
Meeting Room Booking System — FastAPI Backend (V3 Fully Optimized)
"""

from __future__ import annotations
import os
import json
from datetime import datetime, date, timedelta
from typing import List, Optional

import pymysql
import pymysql.cursors
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dbutils.pooled_db import PooledDB

# ─────────────────────────────────────────────
#  DATABASE CONNECTION POOL SETUP (เสถียรที่สุด)
# ─────────────────────────────────────────────
pool = PooledDB(
    creator=pymysql,
    maxconnections=10,
    mincached=2,
    maxcached=5,
    maxshared=3,          # จำกัดการแชร์ท่อเพื่อความเสถียร
    blocking=True,        # ถ้าท่อเต็ม ให้รอจนกว่าจะมีท่อว่าง (ลดอาการ Error)
    ping=1,               # 📌 เช็คท่อทุกครั้งก่อนใช้งาน (แก้ปัญหาต้องกดซ้ำข้อมูลถึงจะขึ้น)
    host=os.environ.get('DB_HOST', 'localhost'),
    port=int(os.environ.get('DB_PORT', 4000)),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', ''),
    database=os.environ.get('DB_DATABASE', 'test'),
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
    ssl={'ssl_verify_cert': True, 'ssl_verify_identity': True}
)

def get_conn():
    return pool.connection()

app = FastAPI(title="Meeting Room API", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/", include_in_schema=False)
def root():
    return FileResponse("index.html")

# ─────────────────────────────────────────────
#  MODELS
# ─────────────────────────────────────────────
class BookingCreate(BaseModel):
    user_id: int; room_id: int; title: str; start_datetime: str; end_datetime: str
    require_break: bool = False; break_note: Optional[str] = ""; note: Optional[str] = ""
    attendee_emails: List[str] = []; equipment_ids: List[int] = []

class RoomUpdate(BaseModel):
    room_name: Optional[str] = None; capacity: Optional[int] = None; location_floor: Optional[str] = None

class EquipmentCreate(BaseModel):
    name: str; type: str; room_id: Optional[int] = None; is_room_fixed: bool = False; status: str = "available"; description: Optional[str] = ""

class EquipmentUpdate(BaseModel):
    name: Optional[str] = None; type: Optional[str] = None; room_id: Optional[int] = None; is_room_fixed: Optional[bool] = None; status: Optional[str] = None; description: Optional[str] = None

def _serialize(row: dict) -> dict:
    for k, v in row.items():
        if isinstance(v, (datetime, date)): row[k] = v.isoformat()
    return row

# ─────────────────────────────────────────────
#  OPTIMIZED ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/api/rooms")
def list_rooms():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.*, e.equipment_id, e.name AS eq_name, e.type AS eq_type, e.status AS eq_status
                FROM room r
                LEFT JOIN equipment e ON r.room_id = e.room_id AND e.is_room_fixed = TRUE
                ORDER BY r.capacity DESC
            """)
            rows = cur.fetchall()
            rooms_dict = {}
            for row in rows:
                rid = row["room_id"]
                if rid not in rooms_dict:
                    rooms_dict[rid] = _serialize({k: v for k, v in row.items() if not k.startswith("eq_")})
                    rooms_dict[rid]["equipment"] = []
                if row["equipment_id"]:
                    rooms_dict[rid]["equipment"].append({
                        "id": row["equipment_id"], "name": row["eq_name"], 
                        "type": row["eq_type"], "status": row["eq_status"]
                    })
        return {"rooms": list(rooms_dict.values())}
    finally:
        conn.close()

@app.get("/api/rooms/availability")
def rooms_availability(check_date: str = Query(...), start_time: str = Query("08:00"), end_time: str = Query("17:00")):
    start_dt = datetime.strptime(f"{check_date} {start_time}", "%Y-%m-%d %H:%M")
    end_dt   = datetime.strptime(f"{check_date} {end_time}",   "%Y-%m-%d %H:%M")
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.*, b.booking_id, b.title AS b_title, b.start_datetime AS b_start, b.end_datetime AS b_end,
                       e.name AS eq_name, e.status AS eq_status
                FROM room r
                LEFT JOIN booking b ON r.room_id = b.room_id AND b.status IN ('confirmed','pending')
                     AND b.start_datetime < %s AND b.end_datetime > %s
                LEFT JOIN equipment e ON r.room_id = e.room_id AND e.is_room_fixed = TRUE
                ORDER BY r.capacity DESC
            """, (end_dt, start_dt))
            rows = cur.fetchall()
            rooms_map = {}
            for row in rows:
                rid = row["room_id"]
                if rid not in rooms_map:
                    rooms_map[rid] = _serialize({k: v for k, v in row.items() if not k.startswith("b_") and not k.startswith("eq_")})
                    rooms_map[rid]["conflicts"] = []; rooms_map[rid]["equipment"] = []
                if row["booking_id"] and not any(x["booking_id"] == row["booking_id"] for x in rooms_map[rid]["conflicts"]):
                    rooms_map[rid]["conflicts"].append(_serialize({
                        "booking_id": row["booking_id"], "title": row["b_title"], 
                        "start_datetime": row["b_start"], "end_datetime": row["b_end"]
                    }))
                if row["eq_name"] and not any(x["name"] == row["eq_name"] for x in rooms_map[rid]["equipment"]):
                    rooms_map[rid]["equipment"].append({"name": row["eq_name"], "status": row["eq_status"]})
                rooms_map[rid]["is_available"] = len(rooms_map[rid]["conflicts"]) == 0
        return {"rooms": list(rooms_map.values())}
    finally:
        conn.close()

@app.get("/api/stats/dashboard")
def dashboard_stats():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 🚀 รวมทุกสถิติไว้ในคำสั่งเดียว เพื่อลด Latency จากสิงคโปร์
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM room) as total_rooms,
                    (SELECT COUNT(*) FROM booking WHERE DATE(start_datetime) = CURDATE() AND status != 'cancelled') as today_bookings,
                    (SELECT COUNT(*) FROM booking WHERE DATE(start_datetime) >= DATE_FORMAT(NOW() ,'%Y-%m-01') AND status != 'cancelled') as month_bookings,
                    (SELECT COUNT(DISTINCT room_id) FROM booking WHERE start_datetime <= NOW() AND end_datetime >= NOW() AND status != 'cancelled') as busy_rooms
            """)
            res = cur.fetchone()
            available_now = res["total_rooms"] - res["busy_rooms"]
            
        return {
            "total_rooms": res["total_rooms"], 
            "available_now": available_now if available_now > 0 else 0, 
            "today_bookings": res["today_bookings"], 
            "month_bookings": res["month_bookings"]
        }
    finally:
        conn.close()

@app.get("/api/bookings")
def list_bookings(user_id: Optional[int] = None, room_id: Optional[int] = None, date_from: Optional[str] = None, date_to: Optional[str] = None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = "SELECT b.*, u.full_name AS booker_name, r.room_name FROM booking b JOIN user u ON b.user_id = u.user_id JOIN room r ON b.room_id = r.room_id WHERE 1=1"
            params = []
            if user_id: sql += " AND b.user_id = %s"; params.append(user_id)
            if room_id: sql += " AND b.room_id = %s"; params.append(room_id)
            if date_from: sql += " AND DATE(b.start_datetime) >= %s"; params.append(date_from)
            if date_to: sql += " AND DATE(b.start_datetime) <= %s"; params.append(date_to)
            cur.execute(sql + " ORDER BY b.start_datetime", params)
            bookings = cur.fetchall()
            for bk in bookings: _serialize(bk)
        return {"bookings": bookings}
    finally:
        conn.close()

@app.post("/api/bookings", status_code=201)
def create_booking(payload: BookingCreate):
    start_dt = datetime.strptime(payload.start_datetime, "%Y-%m-%d %H:%M:%S")
    end_dt   = datetime.strptime(payload.end_datetime,   "%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO booking (user_id, room_id, title, start_datetime, end_datetime, require_break, break_note, note) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (payload.user_id, payload.room_id, payload.title, start_dt, end_dt, payload.require_break, payload.break_note, payload.note))
            bid = cur.lastrowid
            for eq_id in payload.equipment_ids:
                cur.execute("INSERT INTO booking_equipment (booking_id, equipment_id) VALUES (%s,%s)", (bid, eq_id))
        conn.commit()
        return {"booking_id": bid}
    finally:
        conn.close()

@app.get("/api/equipment")
def list_equipment():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM equipment ORDER BY name")
            items = cur.fetchall()
            for i in items: _serialize(i)
        return {"equipment": items}
    finally:
        conn.close()
